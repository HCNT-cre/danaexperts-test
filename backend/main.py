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

# Thiết lập logging
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

# Initialize Voyage AI client
voyage_client = voyageai.Client()

# Đường dẫn đến file database Milvus
DB_PATH = "./milvus_legal.db"

# Xóa database cũ khi khởi động ứng dụng
if os.path.exists(DB_PATH):
    if os.path.isfile(DB_PATH):
        os.remove(DB_PATH)
        logger.info(f"Deleted old database file at {DB_PATH}")
    elif os.path.isdir(DB_PATH):
        shutil.rmtree(DB_PATH)
        logger.info(f"Deleted old database directory at {DB_PATH}")

# Initialize Milvus client với database mới
milvus_client = MilvusClient(uri=DB_PATH)

# Function to create a new collection for a conversation
def create_conversation_collection(conversation_id: str):
    safe_conversation_id = conversation_id.replace("-", "_")
    collection_name = f"legal_rag_collection_{safe_conversation_id}"
    if milvus_client.has_collection(collection_name):
        milvus_client.drop_collection(collection_name)
        logger.info(f"Dropped existing collection: {collection_name}")
    embedding_dim = 1024  # voyage-law-2 model uses 1024 dim
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
        if text.strip():  # Kiểm tra xem text có nội dung không
            embedding = embed_text(text)
            data.append({"id": current_count, "vector": embedding, "text": text})
        else:
            return {"error": "Text content is empty."}
    except Exception as e:
        return {"error": f"Failed to process text: {str(e)}"}

    if data:
        milvus_client.insert(collection_name=collection_name, data=data)

    return {"message": f"Uploaded text to conversation {conversation_id}"}

# Function to rerank retrieved texts based on similarity to query
def rerank_texts(query: str, retrieved_texts: List[str], top_k: int = 5):
    query_embedding = embed_text(query)
    text_embeddings = voyage_client.embed(retrieved_texts, model="voyage-law-2").embeddings
    similarities = [sum(a * b for a, b in zip(query_embedding, text_emb)) for text_emb in text_embeddings]
    sorted_pairs = sorted(zip(retrieved_texts, similarities), key=lambda x: x[1], reverse=True)
    return [pair[0] for pair in sorted_pairs[:top_k]]

# API Chatbot for a specific conversation
@app.get("/chat")
async def chat(conversation_id: str, query: str):
    safe_conversation_id = conversation_id.replace("-", "_")
    collection_name = f"legal_rag_collection_{safe_conversation_id}"

    if not milvus_client.has_collection(collection_name):
        return {"error": f"Conversation {conversation_id} does not exist or has no data."}

    search_res = milvus_client.search(
        collection_name=collection_name,
        data=[embed_text(query)],
        limit=4,
        search_params={"metric_type": "IP", "params": {}},
        output_fields=["text"],
    )

    retrieved_texts = [res["entity"]["text"] for res in search_res[0]]
    if retrieved_texts:
        retrieved_texts = rerank_texts(query, retrieved_texts, top_k=2)
    else:
        return {"response": "No relevant context found for your query."}

    context = "\n\n".join(retrieved_texts)

    SYSTEM_PROMPT = """
    You are a highly knowledgeable legal AI assistant. Your task is to provide accurate and concise answers based solely on the provided legal context. Follow these instructions:
    - Answer the user's question directly and precisely, sticking to the information in the context.
    - Do not hallucinate or provide information outside the given context.
    - Format your response in Markdown:
      - Use **bold** for legal article numbers (e.g., **Điều 630**) and key legal terms.
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
    )

    try:
        response = client.chat.completions.create(
            model="llama3.2:3b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT},
            ],
            max_tokens=1500,
            temperature=0.5,
        )

        answer = response.choices[0].message.content
        return {"response": answer}
    except Exception as e:
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