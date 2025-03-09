# Legal RAG Chatbot

![Legal Chatbot](https://img.shields.io/badge/Legal-Chatbot-blue) ![Python](https://img.shields.io/badge/Python-3.9+-yellow) ![React](https://img.shields.io/badge/React-18.2.0-green) ![License](https://img.shields.io/badge/License-MIT-brightgreen)

A Retrieval-Augmented Generation (RAG) system designed for legal research, integrating Milvus as a vector database, Voyage AI for legal embeddings, and Ollama for local LLM inference. This project includes a React frontend and a FastAPI backend, enabling users to upload legal documents (PDFs) or text, and query legal information efficiently.

This project was inspired by the blog post ["Applying RAG to Legal Data"](https://example.com) by [Author Name], which provided a foundational guide for implementing RAG with legal data.

---

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Features
- **Upload Legal Documents:** Supports uploading PDF files and raw text for indexing.
- **Legal-Specific Embeddings:** Uses Voyage AI's `voyage-law-2` model optimized for legal contexts.
- **Vector Storage:** Stores embeddings in Milvus Lite for efficient retrieval.
- **Conversational Interface:** Chatbot powered by Llama 3.2 (via Ollama) to answer legal queries based on uploaded data.
- **Multi-Conversation Support:** Each conversation has its own isolated collection in Milvus.

---

## Tech Stack
- **Backend:**
  - [FastAPI](https://fastapi.tiangolo.com/): High-performance web framework for building APIs.
  - [Milvus Lite](https://milvus.io/): Lightweight vector database for storing embeddings.
  - [Voyage AI](https://voyageai.com/): Provides legal-specific embeddings.
  - [Ollama](https://ollama.ai/): Local LLM inference with Llama 3.2.
  - [PyPDF](https://pypdf.readthedocs.io/): PDF text extraction.

- **Frontend:**
  - [React](https://reactjs.org/): JavaScript library for building user interfaces.
  - [Material-UI](https://mui.com/): React component library for styling.
  - [axios](https://axios-http.com/): HTTP client for API requests.
  - [react-dropzone](https://react-dropzone.js.org/): File upload handling.

---

## Installation

### Prerequisites
- **Python 3.9+**: For the backend.
- **Node.js 16+**: For the frontend.
- **Ollama**: Install and run locally with Llama 3.2 model (`ollama run llama3.2:3b`).
- **Voyage AI API Key**: Sign up at [Voyage AI](https://voyageai.com/) and get your API key.

### Backend Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/legal-rag-chatbot.git
   cd legal-rag-chatbot/backend