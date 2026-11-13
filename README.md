# 📄 DocuQuery AI — Enterprise Document Intelligence & RAG

A modern, production-grade Retrieval-Augmented Generation (RAG) Document Analyzer. Upload PDFs, TXT, or Markdown files — then ask questions and get answers grounded in your documents, with source citations.

**Frontend:** Pure HTML/CSS/JavaScript on **Vercel** · **Backend:** Python FastAPI on **Render** · **LLM:** OpenRouter API · **Embeddings:** Sentence Transformers `all-MiniLM-L6-v2` · **Vector DB:** FAISS

---

## 🚀 Architecture

| Layer | Technology |
|:---|:---|
| **Frontend** | HTML5 + Tailwind CDN + Vanilla JavaScript |
| **Backend** | FastAPI (ASGI, async) |
| **LLM Inference** | OpenRouter API (Llama 3.3 70B, Claude, Gemini, GPT-4o, etc.) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (384-dim, CPU) |
| **Vector Database** | FAISS (per-document, disk-persisted) |
| **Chat Transport** | Server-Sent Events (SSE) for real-time streaming |
| **Frontend Hosting** | Vercel (static) |
| **Backend Hosting** | Render (web service) |

---

## 📁 Project Structure

```
├── frontend/                       # Static SaaS frontend (deploy to Vercel)
│   ├── index.html                  # Main dashboard
│   ├── css/style.css               # Design system, glassmorphism, animations
│   ├── js/
│   │   ├── config.js               # ← SET YOUR RENDER BACKEND URL HERE
│   │   ├── api.js                  # API client with SSE streaming parser
│   │   └── app.js                  # App logic, DOM events, chat UI
│   └── vercel.json                 # Vercel deployment config
│
├── backend/                        # FastAPI backend (deploy to Render)
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point, CORS
│   │   ├── config.py               # Pydantic Settings (env vars)
│   │   ├── api/routes/
│   │   │   ├── health.py           # GET /health
│   │   │   ├── documents.py        # Upload, list, get, delete
│   │   │   └── chat.py             # RAG chat + SSE streaming
│   │   ├── services/
│   │   │   ├── openrouter_client.py # OpenRouter HTTP client
│   │   │   ├── llm_service.py      # RAG orchestrator
│   │   │   ├── retrieval_service.py # FAISS vector store manager
│   │   │   ├── document_service.py  # Upload lifecycle & metadata
│   │   │   ├── embedding_service.py # Cached HuggingFace embeddings
│   │   │   └── text_extraction.py   # PDF/TXT/MD loaders
│   │   ├── rag/
│   │   │   ├── chunking.py         # RecursiveCharacterTextSplitter (800/150)
│   │   │   └── prompts.py          # Grounding system prompt
│   │   ├── schemas/                # Pydantic request/response models
│   │   └── core/                   # Exceptions, security helpers
│   ├── requirements.txt
│   ├── render.yaml                 # Render blueprint
│   └── .env.example                # Environment variable template
│
├── tests/                          # Integration tests
│   ├── test_integration.py
│   └── test_chat_rag.py
└── README.md
```

---

## 🛠️ Local Development

### Prerequisites
- Python 3.10+ (3.11 recommended)
- OpenRouter API key — get one at [openrouter.ai/keys](https://openrouter.ai/keys)

### Setup

```bash
# 1. Clone and create virtualenv
git clone <your-repo-url>
cd "Document Question Answering system"
python -m venv venv

# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and set your OPENROUTER_API_KEY
```

### Run Locally

```bash
# Start the backend (from project root)
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open `frontend/index.html` directly in your browser, OR serve it:

```bash
# Optional: serve frontend with Python's built-in HTTP server
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

The frontend auto-detects `http://127.0.0.1:8000` as the backend when running locally.

- **Swagger Docs:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/health

---

## 🚢 Production Deployment

### Step 1: Deploy Backend to Render

1. Push your repo to GitHub.
2. Go to [dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service**.
3. Connect your GitHub repository.
4. Configure:

| Setting | Value |
|:---|:---|
| **Name** | `document-analyzer-api` (or anything you like) |
| **Root Directory** | `backend` |
| **Environment** | Python |
| **Python Version** | `3.11.9` |
| **Build Command** | `pip install --upgrade pip && pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | Free (or Starter for persistence) |

5. Set **Environment Variables** in Render dashboard:

| Variable | Value |
|:---|:---|
| `OPENROUTER_API_KEY` | `sk-or-v1-your-key-here` (set as secret) |
| `OPENROUTER_MODEL` | `meta-llama/llama-3.3-70b-instruct:free` |
| `FRONTEND_ORIGIN` | `*` (or your exact Vercel URL after Step 2) |
| `DATA_DIR` | `./data` |
| `ENVIRONMENT` | `production` |
| `PYTHON_VERSION` | `3.11.9` |

6. Click **Deploy**. Wait for the build to finish (~3–8 minutes).
7. Test: visit `https://<your-app>.onrender.com/health` — you should see a JSON response.
8. **Copy your Render URL** — you'll need it for the frontend config.

> **⚠️ Build Command Note:** The `torch --index-url .../cpu` flag installs CPU-only PyTorch (~200MB instead of 2GB). This is critical for Render free tier builds to succeed within the memory and time limits.

---

### Step 2: Deploy Frontend to Vercel

1. **Before deploying**, update `frontend/js/config.js` with your Render backend URL:

```javascript
window.BACKEND_URL = 'https://your-render-app.onrender.com';
```

2. Commit and push.
3. Go to [vercel.com](https://vercel.com) → **Add New** → **Project**.
4. Import your GitHub repository.
5. Configure:

| Setting | Value |
|:---|:---|
| **Root Directory** | `frontend` |
| **Framework Preset** | `Other` |
| **Build Command** | *(leave empty)* |
| **Output Directory** | `.` |

6. Click **Deploy**.
7. Your frontend is live at `https://<your-app>.vercel.app`.

---

### Step 3: Post-Deploy Configuration

After both services are deployed:

1. **(Recommended)** Set `FRONTEND_ORIGIN` on Render to your exact Vercel URL:
   ```
   https://your-app.vercel.app
   ```
   This locks down CORS to only your frontend. Then trigger a Render redeploy.

2. **(Optional)** Update `OPENROUTER_SITE_URL` on Render to your Vercel URL — this shows up in your OpenRouter dashboard for request tracking.

---

## ⚠️ Important Notes

### Render Free Tier Limitations

| Limitation | Impact |
|:---|:---|
| **Cold starts** | After ~15 min of inactivity, Render spins down the service. First request takes ~30–60 seconds. |
| **Ephemeral filesystem** | Uploaded documents and FAISS indexes are **lost on every restart/redeploy**. Re-upload after each restart. |
| **512MB RAM** | Sufficient for `all-MiniLM-L6-v2` + FAISS with moderate document sizes. |

**To persist data:** Upgrade to a paid Render plan (\$7/month) and add a Persistent Disk. Set `DATA_DIR=/var/data` and uncomment the `disk` section in `render.yaml`.

### Frontend Configuration

The frontend reads the backend URL from (in order of priority):
1. `localStorage` — set via the **Settings gear icon** in the UI
2. `window.BACKEND_URL` — set in `frontend/js/config.js`
3. Auto-detection for `localhost` development

---

## 📡 API Reference

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/health` | Health check, version, OpenRouter status |
| `POST` | `/api/documents/upload` | Upload PDF/TXT/MD (multipart form) |
| `GET` | `/api/documents` | List all documents with metadata |
| `GET` | `/api/documents/{id}` | Get document details |
| `DELETE` | `/api/documents/{id}` | Delete document + vectors + chat history |
| `POST` | `/api/chat` | Standard RAG query (JSON response) |
| `POST` | `/api/chat/stream` | Streaming RAG query (SSE) |
| `GET` | `/api/chat/history/{id}` | Get conversation history |
| `DELETE` | `/api/chat/history/{id}` | Clear conversation history |
| `GET` | `/api/chat/models` | List available OpenRouter models |

---

## 🧪 Testing

```bash
# From project root, with venv activated:
python tests/test_integration.py
python tests/test_chat_rag.py
```

Tests verify: health endpoint, PDF upload, text extraction, chunking, embedding, FAISS indexing, similarity search, prompt formatting, source citations, and cleanup.

---

## 📄 License

MIT License.
