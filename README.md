# RAG Chat System

A production-grade Retrieval-Augmented Generation (RAG) chat system built with Django, React, LangChain, and FAISS. Users upload documents into a knowledge base and ask questions; the AI answers strictly from those documents with source citations.

---

## Features

- **RAG pipeline** — LangChain + FAISS vector store + OpenAI embeddings (`text-embedding-3-small`)
- **Streaming responses** — Server-Sent Events (SSE) for real-time token streaming
- **Document upload** — PDF, TXT, MD, DOCX, CSV via drag-and-drop UI or API
- **Persistent chat sessions** — SQLite-backed session + message history
- **Source citations** — every answer links back to the source document and page number
- **JWT authentication** — login, register, auto-refresh, cross-tab logout sync
- **Security hardening** — prompt injection sanitizer, OpenAI content moderation, rate limiting, middleware body guard
- **Evaluation suite** — RAGAS metrics, Promptfoo red-team, G-Eval LLM-as-Judge

---

## Project Structure

```
.
├── backend/
│   ├── chat/
│   │   ├── models.py          # ChatSession, Message
│   │   ├── views.py           # API endpoints (chat, stream, session, upload, auth)
│   │   ├── serializers.py     # DRF serializers
│   │   ├── rag.py             # RAGSystem — load, embed, retrieve, generate
│   │   ├── sanitizers.py      # Prompt injection regex guard
│   │   ├── moderation.py      # OpenAI moderation API (fail-open)
│   │   ├── middleware.py      # Body size limit, null-byte, scanner UA block
│   │   ├── throttles.py       # Per-scope DRF throttle classes
│   │   └── migrations/
│   ├── core/
│   │   ├── settings.py        # All config — env-driven
│   │   └── urls.py            # URL routing
│   ├── knowledge_base/        # Drop documents here
│   ├── vector_store/          # FAISS index (auto-generated, git-ignored)
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ChatContainer.jsx   # Main chat UI + document upload
│       │   ├── LoginForm.jsx       # Login / Register toggle
│       │   ├── MessageBubble.jsx
│       │   ├── MessageInput.jsx
│       │   └── SourceCitation.jsx
│       ├── services/
│       │   ├── api.js             # Axios client with JWT interceptors
│       │   └── auth.js            # login, register, logout, token helpers
│       ├── config.js              # API_BASE_URL
│       └── App.jsx                # Auth gate — shows LoginForm or ChatContainer
│
├── evals/
│   ├── datasets/
│   │   ├── golden_qa.json         # 10 ground-truth Q&A pairs
│   │   └── adversarial.json       # 12 injection / jailbreak test cases
│   ├── ragas/
│   │   └── evaluate_ragas.py      # RAGAS metrics runner
│   ├── promptfoo/
│   │   └── promptfooconfig.yaml   # HTTP quality + security tests
│   ├── geval/
│   │   ├── judge.py               # LLM-as-Judge (chain-of-thought scoring)
│   │   └── criteria.py            # Coherence, groundedness, conciseness rubrics
│   └── run_all.py                 # Master runner — exits 1 if thresholds missed
│
└── README.md
```

---

## Quick Start

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.9+ |
| Node.js | 16+ |
| OpenAI API key | Required |

---

### 1 — Backend Setup

```bash
# From repo root
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
```

Edit `backend/.env` — the only required value is your OpenAI key:

```env
OPENAI_API_KEY=sk-...

# These have working defaults for local dev — change for production:
DJANGO_SECRET_KEY=django-insecure-replace-this-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

```bash
# Apply database migrations
python manage.py migrate

# Start the dev server
python manage.py runserver
```

Backend is now running at `http://localhost:8000`.

---

### 2 — Frontend Setup

```bash
# From repo root
cd frontend

npm install
npm run dev
```

Frontend is now running at `http://localhost:5173`.

---

### 3 — Create Your Account

Open `http://localhost:5173` in your browser. You will see the login screen.

Click **Register** to create an account. After registration you are logged in automatically.

> **Admin access**: You can also create a superuser for the Django admin panel (`/admin/`):
> ```bash
> cd backend
> python manage.py createsuperuser
> ```

---

### 4 — Add Documents to the Knowledge Base

**Option A — Drag & drop in the UI**
Click the upload icon in the chat header and drop your files. The vector index rebuilds automatically.

**Option B — Copy files directly**
Drop `.pdf`, `.txt`, `.md`, `.docx`, or `.csv` files into `backend/knowledge_base/`, then restart the server. The index is rebuilt on startup only when files have changed (SHA-256 manifest comparison).

---

## API Reference

All endpoints (except `register` and `token`) require a JWT access token:
```
Authorization: Bearer <access_token>
```

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register/` | Create account — `{"username":"...","password":"..."}` |
| `POST` | `/api/auth/token/` | Get tokens — `{"username":"...","password":"..."}` → `{"access":"...","refresh":"..."}` |
| `POST` | `/api/auth/token/refresh/` | Refresh access token — `{"refresh":"..."}` |
| `POST` | `/api/auth/logout/` | Blacklist refresh token — `{"refresh":"..."}` |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/` | Send message, get full response |
| `POST` | `/api/chat/stream/` | Send message, stream SSE response |
| `POST` | `/api/session/` | Create new chat session |
| `GET`  | `/api/session/<uuid>/` | Get session with all messages |

**Chat request body:**
```json
{
  "user_message": "What is the return policy?",
  "session_id": "optional-uuid"
}
```

**Chat response:**
```json
{
  "answer": "The return policy allows...",
  "sources": ["Policy.pdf - Page 3"],
  "session_id": "550e8400-...",
  "message_id": 42
}
```

**Stream events** (SSE, `text/event-stream`):
```
data: {"t": "chunk", "content": "The return"}
data: {"t": "chunk", "content": " policy allows..."}
data: {"t": "done",  "sources": ["Policy.pdf - Page 3"], "message_id": 42}
```

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/documents/upload/` | Upload files (`multipart/form-data`, field `files`) |

**Upload response:**
```json
{
  "uploaded": ["Policy.pdf", "FAQ.txt"],
  "skipped": [],
  "message": "Documents uploaded and index refreshed."
}
```

---

## Rate Limits

| Scope | Limit |
|-------|-------|
| Anonymous | 10 requests / hour |
| Authenticated (general) | 60 requests / hour |
| Chat endpoints | 20 requests / hour |
| Document upload | 5 requests / hour |

Rate-limited responses return HTTP `429` with a `Retry-After` header.

---

## Security

| Layer | What it does |
|-------|-------------|
| **Prompt sanitizer** | 15 compiled regex patterns block injection, jailbreak, role-override attempts before they reach the LLM |
| **OpenAI moderation** | Free moderation API screens content for hate, self-harm, violence — fail-open (never blocks on API outage) |
| **Middleware guard** | Blocks scanner user-agents (sqlmap, nikto, burpsuite), enforces 16 KB body limit, rejects null bytes |
| **Session IDOR prevention** | Sessions are scoped to `request.user` — accessing another user's session returns 404 |
| **JWT token blacklist** | Logout invalidates the refresh token server-side |
| **CORS** | Only origins listed in `CORS_ALLOWED_ORIGINS` are allowed |

---

## Evaluation Suite

The `evals/` directory contains three complementary eval frameworks. Run them from the repo root after activating the backend venv.

### RAGAS + G-Eval (no server needed)

```bash
# Both suites
python evals/run_all.py

# RAGAS only
python evals/run_all.py --ragas

# G-Eval only
python evals/run_all.py --geval
```

**RAGAS thresholds:**

| Metric | Threshold |
|--------|-----------|
| Faithfulness | > 0.85 |
| Answer relevancy | > 0.80 |
| Context precision | > 0.75 |
| Context recall | > 0.70 |

**G-Eval thresholds:** coherence, groundedness, conciseness all > 3.5 / 5.0

Results are written to `evals/results/`.

### Promptfoo (requires live server + JWT)

```bash
# Get a token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"<user>","password":"<pass>"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access'])")

JWT_TOKEN=$TOKEN npx promptfoo eval --config evals/promptfoo/promptfooconfig.yaml
```

Tests 5 quality Q&A checks + 5 injection/jailbreak security checks against the live API.

---

## Configuration Reference

### RAG parameters (`backend/chat/rag.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chunk_size` | 1000 | Characters per document chunk |
| `chunk_overlap` | 200 | Overlap between adjacent chunks |
| `k` (retrieval) | 3 | Number of chunks returned per query |
| LLM model | `gpt-4o-mini` | Change to `gpt-4o` for higher quality |
| Embedding model | `text-embedding-3-small` | OpenAI embedding model |

### Environment variables (`backend/.env`)

| Variable | Default | Required |
|----------|---------|----------|
| `OPENAI_API_KEY` | — | Yes |
| `DJANGO_SECRET_KEY` | insecure dev key | Yes (prod) |
| `DJANGO_DEBUG` | `True` | No |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | No |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | No |

---

## Architecture

```
Browser
  └─ React (Vite)
       ├─ LoginForm      ← JWT login / register
       ├─ ChatContainer  ← SSE streaming, file upload
       └─ axios (api.js) ← auto-injects Bearer token, refreshes on 401

Django (port 8000)
  ├─ PromptGuardMiddleware  ← body size, null bytes, scanner UAs
  ├─ DRF throttling         ← per-scope rate limits
  ├─ views.py
  │    ├─ sanitize_message()   ← regex injection check
  │    ├─ is_content_safe()    ← OpenAI moderation
  │    └─ RAGSystem.chat_stream()
  └─ RAGSystem (rag.py)
       ├─ FAISS vector store (disk-cached, manifest-based invalidation)
       ├─ OpenAI Embeddings (text-embedding-3-small)
       └─ ChatOpenAI (gpt-4o-mini, streaming=True)
```

---

## Troubleshooting

**Login returns 401 immediately after registering**
The server may still be starting. Wait a moment and retry.

**"No module named 'ragas'" when running evals**
Install eval dependencies:
```bash
pip install "ragas>=0.1.0" "datasets>=2.14.0"
```

**Documents not appearing in answers**
- Check files are in `backend/knowledge_base/` with a supported extension
- Restart the server — the index rebuilds on startup when files change
- Check server logs for PDF loading errors

**CORS errors in browser**
Ensure `CORS_ALLOWED_ORIGINS` in `backend/.env` includes the frontend origin (e.g., `http://localhost:5173`).

**OpenAI API errors**
- Verify `OPENAI_API_KEY` is set in `backend/.env`
- Check your API key has credits at `platform.openai.com`

**Rate limit hit (HTTP 429)**
Wait for the `Retry-After` period shown in the response header. Chat is limited to 20 requests/hour per user.

---

## Production Checklist

- [ ] Set `DJANGO_SECRET_KEY` to a random 50-char string
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Set `DJANGO_ALLOWED_HOSTS` to your domain
- [ ] Set `CORS_ALLOWED_ORIGINS` to your frontend domain only
- [ ] Switch database to PostgreSQL
- [ ] Serve Django with Gunicorn behind Nginx
- [ ] Enable `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` in settings
- [ ] Build the frontend: `npm run build` → deploy `dist/` to a CDN
