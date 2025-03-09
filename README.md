# Legal RAG Chatbot

![Legal Chatbot](https://img.shields.io/badge/Legal-Chatbot-blue) ![Python](https://img.shields.io/badge/Python-3.9+-yellow) ![React](https://img.shields.io/badge/React-18.2.0-green) ![License](https://img.shields.io/badge/License-MIT-brightgreen)

A Retrieval-Augmented Generation (RAG) system designed for legal research, integrating Milvus as a vector database, Voyage AI for legal embeddings, and Ollama for local LLM inference. This project includes a React frontend and a FastAPI backend, enabling users to upload legal documents (PDFs) or text, and query legal information efficiently.

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
- **Conversational Interface:** Chatbot powered by Llama 3.2:3b (via Ollama) to answer legal queries based on uploaded data.
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
- **Ollama**: Install and run locally with Llama 3.2:3b model (`ollama pull llama3.2:3b`).
- **Voyage AI API Key**: Sign up at [Voyage AI](https://voyageai.com/) and get your API key.

### Clone the repository

```bash
git clone https://github.com/HCNT-cre/danaexperts-test.git
cd danaexperts-test
```

### Backend Setup

Set up the backend environment:

```bash
cd backend
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend API will be available at `http://127.0.0.1:8000`.

### Frontend Setup

Set up and start the frontend application:

```bash
cd ../frontend
yarn install
yarn dev
```

Open your browser and navigate to `http://localhost:5173` to access the frontend.

---

## Usage

1. Access the application at `http://localhost:5173`.
2. Upload legal documents (PDFs) or enter raw text through the interface.
3. Ask legal-related questions; the chatbot responds based on your indexed documents.

---

## Project Structure

```plaintext
danaexperts-test/
├── backend/
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── utils/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   └── App.jsx
│   ├── package.json
│   ├── yarn.lock
│   └── vite.config.js
├── .gitignore
└── README.md
```

---

## How It Works

- **Document Upload:** PDFs are parsed and converted into text using PyPDF.
- **Embeddings:** Text segments are embedded with Voyage AI (`voyage-law-2` model).
- **Storage:** Embeddings are stored and indexed in Milvus Lite for fast retrieval.
- **Chatbot Interaction:** Ollama locally runs the Llama 3.2:3b model to generate responses based on relevant retrieved embeddings.

---

## Contributing

Contributions are welcome! Fork the repository, create a feature branch, commit your changes, and open a pull request.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Acknowledgments

- [Voyage AI](https://voyageai.com/) for specialized legal embeddings
- [Ollama](https://ollama.ai/) for accessible local LLM inference
- [Milvus](https://milvus.io/) for efficient vector search capabilities

