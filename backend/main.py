from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pymilvus import MilvusClient
from dotenv import load_dotenv
import voyageai
from openai import OpenAI
import os
from pypdf import PdfReader
from typing import List
import uuid
import shutil
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
VOYAGE_API_KEY = os.getenv('VOYAGE_API_KEY')

# Initialize FastAPI app
app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Voyage AI client (used for both embedding and reranking)
voyage_client = voyageai.Client()

# Path to Milvus database
DB_PATH = "./milvus_legal.db"

# Delete old database file or directory if exists
if os.path.exists(DB_PATH):
    if os.path.isfile(DB_PATH):
        os.remove(DB_PATH)
        logger.info(f"Deleted old database file at {DB_PATH}")
    elif os.path.isdir(DB_PATH):
        shutil.rmtree(DB_PATH)
        logger.info(f"Deleted old database directory at {DB_PATH}")

# Initialize Milvus client
milvus_client = MilvusClient(uri=DB_PATH)

# Function to split text into chunks
def split_text(text: str, chunk_size=3000, chunk_overlap=300): 
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return text_splitter.split_text(text)

# Function to create a new collection for a conversation
def create_conversation_collection(conversation_id: str):
    safe_conversation_id = conversation_id.replace("-", "_")
    collection_name = f"legal_rag_collection_{safe_conversation_id}"
    if milvus_client.has_collection(collection_name):
        milvus_client.drop_collection(collection_name)
        logger.info(f"Dropped existing collection: {collection_name}")
    embedding_dim = 1024  # voyage-law-2 uses 1024 dim
    milvus_client.create_collection(
        collection_name=collection_name,
        dimension=embedding_dim,
        metric_type="IP",
        consistency_level="Strong",
    )
    return collection_name

# Function to get embedding
def embed_text(text: str):
    return voyage_client.embed([text], model="voyage-law-2").embeddings[0]

# API to start a new conversation
@app.get("/start_conversation")
async def start_conversation():
    conversation_id = str(uuid.uuid4())
    collection_name = create_conversation_collection(conversation_id)
    logger.info(f"Started new conversation with ID: {conversation_id}, Collection: {collection_name}")
    return {"conversation_id": conversation_id}

# API to upload PDF files for a specific conversation
@app.post("/upload")
async def upload_files(conversation_id: str, files: List[UploadFile] = File(...)):
    safe_conversation_id = conversation_id.replace("-", "_")
    collection_name = f"legal_rag_collection_{safe_conversation_id}"
    
    if not milvus_client.has_collection(collection_name):
        create_conversation_collection(conversation_id)

    data = []
    current_count = milvus_client.get_collection_stats(collection_name)["row_count"]

    for file in files:
        try:
            if file.content_type == "application/pdf":
                reader = PdfReader(file.file)
                pages = [page.extract_text() for page in reader.pages if page.extract_text()]
                for i, page in enumerate(pages):
                    logger.info(f"Extracted text from {file.filename}, page {i}: {page[:100]}...")
                    embedding = embed_text(page) 
                    data.append({"id": current_count + len(data), "vector": embedding, "text": page})
            else:
                return {"error": f"File {file.filename} is not a PDF."}
        except Exception as e:
            return {"error": f"Failed to process {file.filename}: {str(e)}"}

    if data:
        milvus_client.insert(collection_name=collection_name, data=data)

    return {"message": f"Uploaded {len(files)} PDF files and indexed {len(data)} pages to conversation {conversation_id}"}

# API to upload text for a specific conversation
@app.post("/upload_text")
async def upload_text(conversation_id: str, text: str = Form(...)):
    safe_conversation_id = conversation_id.replace("-", "_")
    collection_name = f"legal_rag_collection_{safe_conversation_id}"
    
    if not milvus_client.has_collection(collection_name):
        create_conversation_collection(conversation_id)

    data = []
    current_count = milvus_client.get_collection_stats(collection_name)["row_count"]

    try:
        if text.strip():
            chunks = split_text(text)  # Split text into chunks if it’s long
            for i, chunk in enumerate(chunks):
                embedding = embed_text(chunk)
                data.append({"id": current_count + i, "vector": embedding, "text": chunk})
        else:
            return {"error": "Text content is empty."}
    except Exception as e:
        return {"error": f"Failed to process text: {str(e)}"}

    if data:
        milvus_client.insert(collection_name=collection_name, data=data)

    return {"message": f"Uploaded text (split into {len(data)} chunks) to conversation {conversation_id}"}

# Function to rerank retrieved texts using Voyage Reranker
def rerank_texts(query: str, retrieved_texts: List[str], top_k: int = 3):
    # Call Voyage AI rerank API
    reranking = voyage_client.rerank(
        query=query,
        documents=retrieved_texts,
        model="rerank-2",  # Use "rerank-2-lite" if latency is a priority
        top_k=top_k,
        truncation=True  # Automatically truncate if exceeding token limits
    )
    # Return the reranked list of documents
    return [result.document for result in reranking.results]

# API Chatbot for a specific conversation
@app.get("/chat")
async def chat(conversation_id: str, query: str):
    safe_conversation_id = conversation_id.replace("-", "_")
    collection_name = f"legal_rag_collection_{safe_conversation_id}"

    if not milvus_client.has_collection(collection_name):
        return {"error": f"Conversation {conversation_id} does not exist or has no data."}

    # Automatically clarify the query if it’s vague
    if "tóm tắt văn bản này" in query.lower():
        query = "Tóm tắt nội dung chính của văn bản"

    search_res = milvus_client.search(
        collection_name=collection_name,
        data=[embed_text(query)],
        limit=10,  # Increase limit to retrieve more results
        search_params={"metric_type": "IP", "params": {}},
        output_fields=["text"],
    )

    retrieved_texts = [res["entity"]["text"] for res in search_res[0]]
    logger.info(f"Retrieved {len(retrieved_texts)} texts: {retrieved_texts}")
    if retrieved_texts:
        # Use Voyage Reranker instead of CrossEncoder
        retrieved_texts = rerank_texts(query, retrieved_texts, top_k=3)  # Get top 3 after reranking
    else:
        return {"response": "No relevant context found for your query."}

    context = "\n\n".join(retrieved_texts)
    logger.info(f"Final context for query '{query}': {context[:200]}...")

    SYSTEM_PROMPT = """
    You are a highly knowledgeable legal AI assistant. Your task is to provide accurate and concise answers based solely on the provided legal context. Follow these instructions:
    - Answer the user's question directly and precisely, sticking to the information in the context.
    - Do not hallucinate or provide information outside the given context.
    - Format your response in Markdown:
      - Use **bold** for legal article numbers and key legal terms.
      - Use numbered lists (1., 2., etc.) or bullet points (- ) for conditions, steps, or items.
      - Add line breaks between sections for readability.
    - If the context does not contain enough information to fully answer the question, state this clearly and suggest how the user can refine their query.
    """

    USER_PROMPT = f"""
    <context>
    {context}
    </context>
    <question>
    {query}
    </question>
    """

    client = OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama',
        timeout=30,  # Increase timeout
        max_retries=5  # Increase number of retries
    )

    try:
        response = client.chat.completions.create(
            model="llama3.2:3b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT},
            ],
            max_tokens=50000,
            temperature=0.5,
        )

        answer = response.choices[0].message.content
        return {"response": answer}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return {"response": f"Error processing the request: {str(e)}"}

# Optional: API to delete a conversation
@app.delete("/delete_conversation")
async def delete_conversation(conversation_id: str):
    safe_conversation_id = conversation_id.replace("-", "_")
    collection_name = f"legal_rag_collection_{safe_conversation_id}"
    if milvus_client.has_collection(collection_name):
        milvus_client.drop_collection(collection_name)
        return {"message": f"Conversation {conversation_id} deleted."}
    return {"error": f"Conversation {conversation_id} does not exist."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)