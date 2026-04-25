# DocuChat — RAG Chatbot

A Django + React RAG application that lets users chat with uploaded documents via OpenAI GPT-4o-mini and FAISS vector search.

## Project Structure

```
backend/          Django REST API (port 8000)
frontend/         React + Vite SPA (port 5173)
evals/            RAGAS / G-Eval / promptfoo evaluation suite
```

## Running the App

**Backend**
```bash
cd backend
venv/Scripts/activate          # Windows
python manage.py migrate
python manage.py runserver
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` → `http://localhost:8000`, so the frontend `.env` uses `VITE_API_URL=/api`.

## Key Files

| Path | Purpose |
|---|---|
| `backend/chat/rag.py` | RAG system — embeddings, FAISS, LLM calls |
| `backend/chat/views.py` | All API endpoints (auth, chat, admin, upload) |
| `backend/core/settings.py` | Django config — CORS, JWT, throttling |
| `backend/core/urls.py` | URL routing |
| `backend/.env` | Secrets and runtime config |
| `frontend/src/services/api.js` | Axios client + streaming chat |
| `frontend/src/components/ChatContainer.jsx` | Main chat UI |

## Environment Variables (`backend/.env`)

| Variable | Required | Notes |
|---|---|---|
| `OPENAI_API_KEY` | Yes | GPT-4o-mini + text-embedding-3-small |
| `DJANGO_SECRET_KEY` / `SECRET_KEY` | Yes (prod) | Either name works; `DJANGO_*` wins when both are set |
| `DJANGO_DEBUG` / `DEBUG` | No | Defaults to `True` |
| `DJANGO_ALLOWED_HOSTS` / `ALLOWED_HOSTS` | No | Comma-separated; defaults to `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | No | Defaults to `http://localhost:5173` |
| `OPENAI_PROXY` | No | HTTP proxy for OpenAI API (e.g. `http://127.0.0.1:7890`) — set this if `api.openai.com` is blocked |

## Known Issue — OpenAI API Blocked

`api.openai.com` returns HTTP 000 (unreachable) on this machine while general internet works. Every LLM and embedding call will time out until this is resolved.

**Fix:** Set `OPENAI_PROXY` in `backend/.env` to a working HTTP/SOCKS proxy or enable a VPN before starting the backend.

```
OPENAI_PROXY=http://127.0.0.1:7890
```

The `_openai_kwargs()` helper in `rag.py` picks this up and passes an `httpx.Client` with the proxy to all OpenAI/LangChain clients.

## Architecture

1. User sends message → `POST /api/chat/stream/` (SSE)
2. Backend sanitizes + moderates message
3. `RAGSystem.chat_stream()` retrieves top-3 FAISS chunks, streams GPT-4o-mini response token-by-token
4. Frontend reads SSE stream and updates the chat bubble in real time

**Vector store:** FAISS index in `backend/vector_store/faiss_index/`. Rebuilt automatically when knowledge base files change (hash-based manifest). Documents live in `backend/knowledge_base/`.

## Auth

JWT (SimpleJWT). Access token: 60 min. Refresh: 7 days with rotation. First registered user is auto-promoted to admin.

## Common Commands

```bash
# Rebuild FAISS index (after adding files manually)
cd backend && venv/Scripts/python manage.py shell -c "from chat.rag import reload_rag_system; reload_rag_system()"

# Run evals
python evals/run_all.py
```
