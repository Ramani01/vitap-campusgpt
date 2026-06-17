# CampusGPT 🎓

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-blue?style=for-the-badge&logoColor=white)](https://www.trychroma.com/)
[![Gemini](https://img.shields.io/badge/LLM-Gemini_Cloud-orange?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Cloudflare](https://img.shields.io/badge/Tunnel-Cloudflare-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)](https://www.cloudflare.com/)

**CampusGPT** is a production-ready, feature-rich **Retrieval-Augmented Generation (RAG) assistant** specifically built for navigating regulations, policies, schedules, and code-of-conduct documents at **VIT-AP University**. It employs an advanced search pipeline combining hybrid retrieval, neural reranking, local/cloud model switching, and automated document synchronization.

---

## 🚀 Key Features

*   🔍 **Advanced Hybrid Retrieval Pipeline**: Integrates dense vector search (using `sentence-transformers` embeddings in ChromaDB) and sparse lexical search (using `BM25Okapi`) to retrieve highly relevant context.
*   🥇 **Cross-Encoder Reranking**: Utilizes the `ms-marco-MiniLM-L-6-v2` cross-encoder to re-score and re-rank the retrieved passages for maximum context accuracy.
*   🧠 **Flexible LLM Architectures**:
    *   **Cloud Mode**: Uses Google's **Gemini 2.5 Flash** for quick, high-quality, and robust answers.
    *   **Local Mode**: Fallback to local model execution via **Ollama** (e.g., `qwen2.5:3b`) or **fine-tuned local models** (supports PEFT LoRA adapters / full-model checkpoints loaded on CPU).
*   🔄 **Dynamic Document Syncing**: Automatically monitors the `campusgpt/data/pdfs/` folder for changes. Adding, modifying, or removing a PDF prompts incremental extraction (via `pypdf`) and updating of text chunks in ChromaDB and BM25.
*   📝 **Smart Response Sanitizer**: Contains post-processing rules to clean up hallucinations of document paths, strip raw references (e.g. `[1]`, `VIT-AP-Academic-Regulations.pdf`), and filter out pure reference/metadata statements to provide clean, natural-language answers.
*   🛡️ **Safety Guardrails**: Implements query validation, query length checks (< 500 characters), response content checks, and semantic context filtering.
*   🎨 **Premium Dark UI**: Responsive, modern glassmorphic web dashboard with chat-history persistence, real-time backend/Ollama status indicators, and slider-adjustable RAG parameters.

---

## 📂 Project Structure

```text
├── campusgpt/                    # Core FastAPI backend & Frontend assets
│   ├── data/
│   │   └── pdfs/                 # VIT-AP policy documents (PDF format)
│   ├── extracted/                # Extracted text outputs from PDFs
│   ├── scripts/                  # Testing and evaluation utilities
│   ├── app.py                    # Main FastAPI server (APIs, RAG pipeline, Guardrails)
│   ├── app.js                    # UI Interaction & REST requests logic
│   ├── index.html                # Frontend entry layout (Glassmorphism layout)
│   ├── style.css                 # Custom styled dark aesthetics
│   ├── build_db.py               # Offline ChromaDB creation script
│   ├── requirements.txt          # Python packages list
│   └── Dockerfile                # Multi-stage production container setup
├── campusgpt_hf/                 # Mirror repository optimized for Hugging Face Spaces
├── docker-compose.yml            # Multi-container orchestration (FastAPI + Nginx + Cloudflare)
├── nginx.conf                    # Nginx configuration (serving static assets & API reverse-proxy)
├── .gitignore                    # Project rules for excluding caches and local credentials
└── README.md                     # Project documentation (This file)
```

---

## ⚙️ Configuration & Environment Variables

Create a file named `.env` in the `campusgpt/` directory (or workspace root if running Docker Compose) to configure settings.

```env
# Google Gemini API Credentials
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE

# Ollama Endpoint Configuration (For local fallbacks)
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:3b

# ChromaDB Custom Collection Name
CHROMA_COLLECTION=vitap
```

---

## 🛠️ Local Setup Guide

### Method 1: Docker Compose (Recommended)
This instantiates a full-stack environment consisting of:
1.  **FastAPI Backend** (Port `7860`)
2.  **Nginx Server** (Port `80` - serves the HTML/CSS/JS frontend directly and proxies api requests)
3.  **Cloudflare Tunnel** (automatically provisions a temporary public URL to access your chatbot from anywhere!)

To run using Docker Compose:
1. Make sure you have Docker and Docker Compose installed.
2. Place your `.env` file in `./campusgpt/` containing your `GEMINI_API_KEY`.
3. Run the following command:
   ```bash
   docker-compose up --build -d
   ```
4. Access the web app at `http://localhost`.

---

### Method 2: Manual Installation

#### 1. Setup Virtual Environment
```bash
# Clone the repository and navigate to the directory
cd campusgpt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Index Documents
Place your university PDF documents inside `campusgpt/data/pdfs/` and run the offline builder to generate the database:
```bash
python build_db.py
```

#### 3. Run Server
Launch the development server via Uvicorn:
```bash
uvicorn app:app --host 0.0.0.0 --port 7860 --reload
```
Open your browser and navigate to `http://localhost:7860` to use the chatbot.

---

## ⚙️ RAG Customization Settings

CampusGPT features an **Agentic RAG Settings** panel directly in the UI where you can configure the search pipeline parameters in real-time:
*   **Agentic RAG Mode (Toggle)**: Enable/disable retrieval-augmentation. Disabling queries the LLM directly without local context.
*   **Category Filters**: Limit vector search results to specific document domains (e.g. `Academic`, `Hostel`, `Ethics`, `Admissions`, `Administration`).
*   **Document Type Filters**: Filter by document type (e.g. `Policy`, `Schedule`, `Affidavit`, `Brochure`).
*   **Context Chunks (Slider)**: Configure the top-$k$ limit of document snippets to feed into the prompt context (1 to 10 chunks).
*   **Hybrid Search (Toggle)**: Turn off to rely purely on Dense Vector Search, or turn on to enable combined BM25 search.
*   **Cross-Encoder Reranking (Toggle)**: Enable or disable the CPU-based MS-Marco reranking step.
*   **Query Optimizer (Toggle)**: Toggle LLM-powered query expansion/rewriting prior to querying ChromaDB.

---

## 🧪 Development & Testing Scripts

Inside `campusgpt/scripts/` are a few utility scripts you can execute for diagnostics:
*   `test_local_server.py`: Runs basic checks on the local FastAPI endpoints.
*   `test_query.py`: Directly queries the backend engine from command line to verify RAG response quality.
*   `test_api_models.py`: Verifies connections and response capabilities of Ollama and Gemini API.
*   `test_cleaner_new.py`: Inspects string post-processing cleaner rules on simulated LLM outputs.

---

## 🤗 Deployment to Hugging Face Spaces

This project contains a mirror version in `campusgpt_hf` configured with a custom `Dockerfile` ready to deploy directly as a Hugging Face Space using the Docker SDK:
1. Create a new Space on [Hugging Face](https://huggingface.co/new-space).
2. Choose **Docker** as the SDK.
3. Push the files under `campusgpt_hf` to the Space repository or link it to your GitHub repo.
4. Set the `GEMINI_API_KEY` repository secret in the Space Settings page for cloud generation support.
