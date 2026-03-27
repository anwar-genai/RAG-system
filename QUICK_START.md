# Quick Start Guide - RAG Chat System

Get your RAG chat system running in 10 minutes!

## Prerequisites

- ✅ Python 3.9+ installed
- ✅ Node.js 16+ installed
- ✅ OpenAI API key (get one at https://platform.openai.com/account/api-keys)

## Step 1: Get Your OpenAI API Key (2 minutes)

1. Go to https://platform.openai.com/account/api-keys
2. Click "Create new secret key"
3. Copy the key (you won't see it again!)
4. Keep it safe - you'll need it in Step 3

## Step 2: Setup Backend (3 minutes)

### Windows:
```bash
# Run the setup script
setup.bat
```

### macOS/Linux:
```bash
# Run the setup script
chmod +x setup.sh
./setup.sh
```

### Manual Setup (if scripts don't work):
```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

## Step 3: Configure OpenAI API Key (1 minute)

Edit `backend/.env` and add your API key:

```
OPENAI_API_KEY=sk-your-key-here-12345...
```

Save the file.

## Step 4: Start Backend Server (1 minute)

```bash
cd backend
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
```

✅ Backend is running at `http://localhost:8000`

## Step 5: Setup Frontend (2 minutes)

Open **a new terminal** (keep the backend running):

```bash
cd frontend
npm install
```

This installs React and dependencies.

## Step 6: Start Frontend Server (1 minute)

```bash
npm run dev
```

You should see:
```
  Local:   http://localhost:5173/
```

✅ Frontend is running at `http://localhost:5173`

## Step 7: Open in Browser

1. Open your browser
2. Go to `http://localhost:5173`
3. You should see the RAG Chat interface! 🎉

## Step 8: Test the System

### Option A: Test with Demo Mode
The system starts with a demo that works without any PDFs.
Try asking: "What information do you have?"

### Option B: Add Sample PDFs (Optional)

Make sure **backend is running**, then in a new terminal:

```bash
cd backend
pip install reportlab
python generate_sample_pdfs.py
```

This creates sample PDFs in `backend/knowledge_base/`:
- Company_Handbook.pdf
- Product_Guide.pdf
- FAQ.pdf

📝 **Restart the backend server** for changes to take effect!

Now try asking questions about the company handbook, products, or FAQs!

## Testing Questions

Ask these in the chat to test the RAG system:

With sample PDFs:
- "What are the core values?"
- "What is the product guide about?"
- "Tell me about pricing plans"
- "How do I cancel my subscription?"
- "What payment methods do you accept?"

## Troubleshooting

### "Connection refused" error
- Make sure the backend is running (`python manage.py runserver`)
- Check it's on port 8000: `http://localhost:8000`

### "OpenAI API Error"
- Check your API key in `backend/.env`
- Make sure it starts with `sk-`
- Verify you have API credits: https://platform.openai.com/account/billing/limits

### PDFs not loading
- Place PDF files in `backend/knowledge_base/`
- Restart the Django server
- Check the server output for errors

### Port already in use
- Backend port 8000: `lsof -i :8000` (macOS/Linux) or kill other processes
- Frontend port 5173: `lsof -i :5173` (macOS/Linux) or kill other processes
- Or run on different ports with `--port` flag

## Next Steps

1. **Add Your Documents**: Place any PDF in `backend/knowledge_base/`
2. **Customize UI**: Edit `frontend/src/styles/` for colors/fonts
3. **Adjust RAG**: Edit `backend/chat/rag.py` for context size, model, etc.
4. **Deploy**: See full README.md for production deployment

## Full Documentation

For detailed information, see [README.md](README.md)

## API Endpoints

Once backend is running, test the API directly:

### Create a session
```bash
curl -X POST http://localhost:8000/api/session/
```

### Send a message
```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"user_message": "Hello!", "session_id": null}'
```

## File Structure

```
RAG/
├── backend/                    # Django backend
│   ├── chat/
│   │   ├── models.py          # Database models
│   │   ├── views.py           # API endpoints
│   │   ├── rag.py             # RAG system
│   │   └── serializers.py
│   ├── knowledge_base/        # Your PDF documents
│   ├── manage.py
│   ├── requirements.txt
│   └── .env                   # Your API key here
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # Chat UI components
│   │   ├── services/          # API client
│   │   ├── styles/            # CSS styles
│   │   └── App.jsx
│   ├── package.json
│   └── .env
│
├── README.md                  # Full documentation
├── setup.bat                  # Windows setup
└── setup.sh                   # macOS/Linux setup
```

## Getting Help

1. Check the [README.md](README.md) for complete documentation
2. Review console logs in both terminals
3. Check browser console (F12 → Console tab)
4. Verify all prerequisites are installed

---

**You're all set! 🚀**

The RAG Chat System is now running with:
- ✅ AI-powered chat with document understanding
- ✅ Real-time responses with source citations
- ✅ Persistent chat history
- ✅ Beautiful chat UI

Happy chatting! 💬
