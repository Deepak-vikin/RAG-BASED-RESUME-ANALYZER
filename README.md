# 📄 DocuQuery AI — Enterprise Document Intelligence & RAG

A modern, production-grade Retrieval-Augmented Generation (RAG) Document Analyzer application. Completely migrated from legacy Streamlit + Ollama to a high-performance **FastAPI** backend powered by **OpenRouter API** and a dedicated, responsive **HTML5/CSS3/JavaScript** SaaS dashboard deployable to **Vercel** and **Render**.

---

## 🚀 Key Highlights & Architecture Migration

| Feature | Legacy Implementation | Modernized Production Stack |
| :--- | :--- | :--- |
| **Frontend** | Streamlit Python script | Pure **HTML5 + Modern CSS + Vanilla JavaScript** with Tailwind CDN & Glassmorphic dark SaaS UI |
| **LLM Inference** | Local Ollama (`llama3`) | **OpenRouter API** with configurable models (Llama 3.3 70B, Claude 3.5 Sonnet, Gemini 2.0 Flash, GPT-4o Mini) |
| **Backend** | Single monolithic script | Modular **FastAPI** ASGI architecture with strict schemas, exception handling & CORS |
| **Embeddings** | SentenceTransformers | **`sentence-transformers/all-MiniLM-L6-v2`** (384-dim, CPU-optimized, cached singleton) |
| **Vector Database** | In-memory ephemeral FAISS | **Persistent Disk FAISS** per-document stores with cross-document aggregation & safe cleanup |
| **Chat Interaction** | Blocking re-runs | **Real-time Server-Sent Events (SSE)** streaming with interactive source citation modals |
| **Deployment** | Local only | **Render** (Backend API + Persistent Disk) & **Vercel** (Frontend static SPA) |

---

## 🌟 Features

### 🖥️ 1. Modern SaaS Frontend Interface
- **Zero Node.js / Zero TypeScript overhead**: Pure HTML, CSS, and Vanilla JavaScript with instant load times and zero build steps.
- **Dark Theme & Ambient Aesthetics**: Floating animated gradient orbs, glassmorphic cards, crisp borders, and JetBrains Mono code styling.
- **Document Management**: Drag-and-drop document upload with format tags (`.pdf`, `.txt`, `.md`), file size validation (up to 30MB), indexing progress indicators, and instant deletion.
- **Two-Panel Workspace**:
  - **Left Panel**: Document library, page/chunk counters, selection for scoped queries, or "All Documents" mode.
  - **Right Panel**: Conversational AI assistant with real-time SSE streaming, Markdown rendering (`marked.js`), one-click response copy, and collapsible citation badges.
- **Grounding Citations**: Click on any source chip to inspect the exact document excerpt, page number, and chunk index used to synthesize the answer.
- **Model Switcher**: Dynamic dropdown to switch between Llama 3.3 70B, Claude 3.5 Sonnet, Gemini 2.0 Flash, GPT-4o Mini, and free-tier models on the fly.

### 🧠 2. Production RAG & AI Pipeline
- **Strict Grounding Rules**: Strict system prompts prevent the model from hallucinating or inventing facts not in the context. If an answer cannot be deduced from the document, it explicitly states so.
- **Scoped & Global Retrieval**: Query against an individual selected document or search across all uploaded documents simultaneously.
- **Persistence Strategy**: FAISS vector indices and uploaded documents are stored in a configurable storage directory (`DATA_DIR`), fully compatible with Render Persistent Disks (`/var/data`).
- **Resilience**: Comprehensive error handling for rate limits, model overloads, timeouts, and missing API credentials.

---

## 📁 Project Structure

```
Document Question Answering system/
│
├── frontend/                     # Pure HTML5 / CSS / Vanilla JS Frontend
│   ├── index.html                # Main application dashboard
│   ├── css/
│   │   └── style.css             # Custom design system, animations & glassmorphism
│   ├── js/
│   │   ├── api.js                # API client with auto-detection & SSE streaming
│   │   └── app.js                # Application state, DOM events & chat logic
│   └── vercel.json               # Vercel static deployment configuration
│
├── backend/                      # Production FastAPI Backend
│   ├── app/
│   │   ├── __init__.py           # Path auto-configuration
│   │   ├── main.py               # FastAPI entry point, CORS & static file mount
│   │   ├── config.py             # Pydantic Settings & environment variables
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── health.py     # GET /health probe
│   │   │       ├── documents.py  # Upload, list, get, delete documents
│   │   │       └── chat.py       # RAG chat & SSE streaming endpoints
│   │   ├── core/
│   │   │   ├── exceptions.py     # Custom exception classes
│   │   │   └── security.py       # Filename sanitization & file validation
│   │   ├── schemas/
│   │   │   ├── document.py       # Pydantic request/response models
│   │   │   └── chat.py           # Chat request, response, and source schemas
│   │   ├── rag/
│   │   │   ├── chunking.py       # RecursiveCharacterTextSplitter (800 / 150)
│   │   │   └── prompts.py        # Strict grounding prompt templates
│   │   └── services/
│   │       ├── text_extraction.py   # PyPDFLoader and text loaders
│   │       ├── embedding_service.py # Cached HuggingFaceEmbeddings singleton
│   │       ├── retrieval_service.py # FAISS vector store manager & retrieval
│   │       ├── openrouter_client.py # HTTP client for OpenRouter API
│   │       ├── llm_service.py       # RAG orchestration & SSE generator
│   │       └── document_service.py  # Metadata tracking & file persistence
│   ├── requirements.txt          # Python dependencies
│   ├── render.yaml               # Render Infrastructure-as-Code blueprint
│   └── .env.example              # Environment variables template
│
├── tests/                        # Automated Integration Tests
│   ├── test_integration.py       # Upload, chunk, index, retrieve & delete tests
│   └── test_chat_rag.py          # End-to-end RAG chat pipeline test
│
├── legacy/                       # Archived Streamlit & Ollama scripts
│   ├── app.py
│   └── rag_engine.py
│
├── requirements.txt              # Root dependencies
├── render.yaml                   # Root Render blueprint
├── .gitignore                    # Git ignore file
└── README.md                     # Documentation
```

---

## 🛠️ Local Development Setup

### 1. Prerequisites
- **Python 3.10+** (Python 3.11 recommended)
- An **OpenRouter API Key** (obtain from [openrouter.ai/keys](https://openrouter.ai/keys))

### 2. Configure Environment Variables
Copy `backend/.env.example` to `backend/.env` (or root `.env`):
```bash
cp backend/.env.example backend/.env
```
Edit `backend/.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
FRONTEND_ORIGIN=*
DATA_DIR=./data
```

### 3. Install Dependencies
```bash
# Using existing virtualenv or create a new one:
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r backend/requirements.txt
```

### 4. Start the Application
Run the FastAPI backend with Uvicorn:
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Once started, visit:
- **Application UI**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) *(FastAPI mounts and serves the frontend automatically!)*
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Alternatively, you can open `frontend/index.html` directly in any web browser or serve it with any static web server (e.g., Python's `python -m http.server 3000` from the `frontend/` directory).

---

## 🚢 Production Deployment

### A. Deploy Backend to Render

1. **Push your repository** to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com), click **New +** → **Blueprint** and select your repository, OR create a **Web Service**:
   - **Root Directory**: `backend`
   - **Environment**: `Python`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **Environment Variables**:
   - `OPENROUTER_API_KEY`: `sk-or-v1-...`
   - `OPENROUTER_MODEL`: `meta-llama/llama-3.3-70b-instruct`
   - `FRONTEND_ORIGIN`: `https://your-frontend.vercel.app` (or `*`)
   - `DATA_DIR`: `/var/data` (if using a persistent disk) or `./data`
4. *(Optional for Persistence)*: On paid plans, add a **Disk** mounted at `/var/data` (e.g. 5GB) so vector stores and uploads persist across redeploys.

---

### B. Deploy Frontend to Vercel

1. In the [Vercel Dashboard](https://vercel.com/dashboard), click **Add New...** → **Project**.
2. Select your repository.
3. Configure project settings:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Other` (Static HTML/CSS/JS)
   - **Build Command**: Leave empty (No build step required)
   - **Output Directory**: `.`
4. Click **Deploy**.
5. Once deployed, open your Vercel URL. Click the **Gear (Settings)** icon in the navigation bar to set your backend URL:
   ```
   https://your-document-analyzer.onrender.com
   ```
   *The URL is automatically saved to `localStorage` and will persist for all future interactions.*

---

## 📡 REST API Reference

### Health
- `GET /health`
  - Returns backend health, version, OpenRouter status, and indexed document count.

### Documents
- `POST /api/documents/upload`
  - Multipart file upload (`.pdf`, `.txt`, `.md`).
  - Automatically extracts text with `PyPDFLoader`, divides into chunks (800 chars / 150 overlap), generates embeddings, and persists FAISS index.
- `GET /api/documents`
  - Lists all uploaded documents with metadata (page count, chunk count, file size, upload timestamp).
- `GET /api/documents/{document_id}`
  - Retrieves specific document details.
- `DELETE /api/documents/{document_id}`
  - Deletes document, disk files, vector indices, and associated conversation history.

### Chat & Question Answering
- `POST /api/chat`
  - Standard JSON RAG query.
  - Body:
    ```json
    {
      "question": "What are the candidate's core skills?",
      "document_id": "optional-document-uuid",
      "model": "meta-llama/llama-3.3-70b-instruct"
    }
    ```
  - Returns: `{ "answer": "...", "sources": [...], "model_used": "..." }`
- `POST /api/chat/stream`
  - Server-Sent Events (SSE) streaming endpoint.
  - Streams retrieved source metadata first, followed by live tokens, and a completion event.
- `GET /api/chat/history/{document_id}`
  - Returns conversation history.
- `DELETE /api/chat/history/{document_id}`
  - Clears conversation history for the specified document or global session.
- `GET /api/chat/models`
  - Returns the list of curated OpenRouter models supported.

---

## 🧪 Testing and Verification

Run the automated integration test suite:
```bash
# Run backend integration tests:
python tests/test_integration.py

# Run RAG chat pipeline tests:
python tests/test_chat_rag.py
```

Both tests verify:
- ✅ Health endpoint returns 200 OK.
- ✅ PDF document upload, PyPDFLoader text extraction, and RecursiveCharacterTextSplitter chunking.
- ✅ Sentence-Transformers embeddings and FAISS index persistence.
- ✅ Accurate vector similarity search (k=5).
- ✅ Grounded prompt formatting and source citation references.
- ✅ Error handling and clean resource deletion.

---

## 📄 License
MIT License.
