# RAG-Based AI Chat System

A professional, production-ready RAG (Retrieval-Augmented Generation) AI chat system built with Django, React, LangChain, and FAISS.

## Features

- ✅ **RAG System**: Retrieval-Augmented Generation using LangChain + FAISS
- ✅ **PDF Knowledge Base**: Automatically load and index PDF documents
- ✅ **Chat History**: Persistent chat sessions stored in database
- ✅ **Source Citations**: AI responses include document sources and page numbers
- ✅ **Conversational Memory**: Maintains context across conversation turns
- ✅ **Modern UI**: ChatGPT-style chat interface built with React
- ✅ **Session Management**: Unique session IDs with chat history persistence
- ✅ **API-Driven**: RESTful API with Django REST Framework

## Project Structure

```
.
├── backend/                          # Django backend
│   ├── chat/                        # Chat app
│   │   ├── models.py               # Database models (ChatSession, Message)
│   │   ├── views.py                # API endpoints
│   │   ├── serializers.py          # DRF serializers
│   │   ├── rag.py                  # RAG system implementation
│   │   └── migrations/
│   ├── core/                        # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py                 # URL routing
│   │   └── wsgi.py
│   ├── knowledge_base/              # PDF knowledge base directory
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── components/              # React components
│   │   │   ├── ChatContainer.jsx   # Main chat component
│   │   │   ├── MessageBubble.jsx   # Message display
│   │   │   ├── MessageInput.jsx    # Input field
│   │   │   └── SourceCitation.jsx  # Source display
│   │   ├── services/                # API services
│   │   │   └── api.js              # API client
│   │   ├── styles/                  # CSS modules
│   │   │   ├── ChatContainer.css
│   │   │   ├── MessageBubble.css
│   │   │   ├── MessageInput.css
│   │   │   └── SourceCitation.css
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── vite.config.js              # Vite config with API proxy
│   ├── package.json
│   └── .env
│
└── README.md
```

## Prerequisites

- Python 3.9+
- Node.js 16+
- OpenAI API key (for GPT models)
- pip (Python package manager)
- npm or yarn (Node package manager)

## Backend Setup

### 1. Create and Activate Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend` directory (copy from `.env.example`):

```bash
cd backend
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your-openai-api-key-here
```

Get your OpenAI API key from: https://platform.openai.com/account/api-keys

### 4. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Add PDF Documents (Optional)

Place any PDF files in the `backend/knowledge_base/` directory. The system will automatically load and index them on startup.

Example documents you can add:
- Company handbooks
- Product documentation
- FAQs
- Technical guides
- Research papers

### 6. Run Development Server

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000/api`

## Frontend Setup

### 1. Install Node Dependencies

```bash
cd frontend
npm install
```

### 2. Configure API Endpoint

The `.env` file is already configured to use the API at `/api`. The Vite dev server will proxy requests to `http://localhost:8000`.

If you need to change the API URL, edit `frontend/.env`:

```
VITE_API_URL=http://localhost:8000/api
```

### 3. Run Development Server

```bash
npm run dev
```

The frontend will be available at: `http://localhost:5173`

## API Endpoints

### Send Message (Chat)

```
POST /api/chat/

Request Body:
{
  "session_id": "optional-uuid",
  "user_message": "Your question here"
}

Response:
{
  "answer": "AI response text",
  "sources": ["Document.pdf - Page 2", "Guide.pdf - Page 5"],
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": 1
}
```

### Get Session

```
GET /api/session/{session_id}/

Response:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "id": 1,
      "message_type": "user",
      "content": "What is in the document?",
      "sources": [],
      "created_at": "2026-02-07T10:00:00Z"
    },
    {
      "id": 2,
      "message_type": "assistant",
      "content": "The document contains...",
      "sources": ["Document.pdf - Page 1"],
      "created_at": "2026-02-07T10:00:05Z"
    }
  ],
  "created_at": "2026-02-07T10:00:00Z",
  "updated_at": "2026-02-07T10:00:05Z"
}
```

### Create Session

```
POST /api/session/

Response:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Usage

1. Open the frontend at `http://localhost:5173` in your browser
2. Start typing your question in the chat input
3. The AI will respond with an answer based on the knowledge base documents
4. Sources are automatically displayed below each AI response
5. Chat history is saved and can be restored using the session ID

## Architecture

### Backend (Django)

- **Models**: `ChatSession` and `Message` for storing chat history
- **RAG System** (`rag.py`):
  - PDF document loading and processing
  - Text chunking with `RecursiveCharacterTextSplitter`
  - FAISS vector store for semantic search
  - OpenAI embeddings and GPT models for responses
  - Conversational memory using last 4 messages for context
- **Views**: REST API endpoints for chat operations
- **Serializers**: Data validation and transformation

### Frontend (React)

- **ChatContainer**: Main component managing chat state and API calls
- **MessageBubble**: For displaying individual messages
- **MessageInput**: For user input with support for multi-line messages
- **SourceCitation**: For displaying source documents
- **API Service**: Axios-based API client for backend communication

## Configuration

### RAG System Parameters

Edit `backend/chat/rag.py` to customize:

- **Chunk Size**: `chunk_size=1000` (split documents into 1000 char chunks)
- **Chunk Overlap**: `chunk_overlap=200` (200 char overlap between chunks)
- **Retrieval K**: `search_kwargs={"k": 3}` (retrieve top 3 relevant chunks)
- **LLM Model**: `model="gpt-4o-mini"` (use different OpenAI models)
- **Temperature**: `temperature=0.7` (response creativity level)

### API Configuration

Edit `backend/core/settings.py`:

- **CORS Settings**: Already allows all origins for demo
- **Database**: Default SQLite, can change to PostgreSQL/MySQL
- **Rest Framework**: Pagination, filtering, authentication settings

## Troubleshooting

### Issue: CORS errors in frontend

**Solution**: The backend already has CORS enabled. Make sure:
- Backend is running on `http://localhost:8000`
- Frontend dev server is running on `http://localhost:5173`
- `django-cors-headers` is installed and configured

### Issue: OpenAI API errors

**Solution**: 
- Ensure `OPENAI_API_KEY` is set in backend `.env` file
- Check that your API key is valid and has credits
- Verify you're using a valid model (gpt-4o-mini, gpt-4, etc.)

### Issue: PDFs not being loaded

**Solution**:
- Place PDF files in `backend/knowledge_base/` directory
- Files must have `.pdf` extension
- Restart the Django server for changes to take effect
- Check console logs for any PDF loading errors

### Issue: Database migrations errors

**Solution**:
```bash
# If migrations fail, try:
python manage.py migrate --fake-initial
python manage.py migrate
```

## Production Deployment

### Backend (Django)

For production deployment:

1. Set `DEBUG=False` in `settings.py`
2. Add your domain to `ALLOWED_HOSTS`
3. Use PostgreSQL instead of SQLite
4. Set secure cookies and HTTPS
5. Use environment variables for secrets
6. Deploy using Gunicorn/uWSGI

### Frontend (React)

Build for production:

```bash
npm run build
```

Deploy the `dist/` folder to a static hosting service or CDN.

## Performance Optimization

- FAISS vector store is in-memory for fast retrieval
- PDFs are cached as embeddings (no re-processing on restart)
- Chat history loaded on-demand per session
- Streaming responses could be added with WebSockets

## Security Considerations

- No authentication in this demo version
- Add session tokens for production
- Validate and sanitize all user inputs
- Rate limit API endpoints
- Use HTTPS in production
- Secure API keys in environment variables

## License

This project is provided as-is for demonstration purposes.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API endpoint documentation
3. Check browser console and server logs for errors
