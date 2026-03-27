# Quick Reference Card

## 🚀 Quick Start (10 minutes)

```bash
# Windows
setup.bat

# macOS/Linux
chmod +x setup.sh
./setup.sh

# Manual (3 steps)
1. cd backend && pip install -r requirements.txt && python manage.py migrate
2. Edit backend/.env - Add OPENAI_API_KEY
3. Run: python manage.py runserver (in backend)
4. Run: npm install && npm run dev (in frontend, new terminal)
5. Open: http://localhost:5173
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `backend/chat/rag.py` | RAG system implementation |
| `backend/chat/models.py` | Database models |
| `backend/chat/views.py` | API endpoints |
| `frontend/src/components/ChatContainer.jsx` | Main chat UI |
| `backend/.env` | Your OpenAI API key (create this!) |
| `backend/knowledge_base/` | Put PDFs here |

---

## 🔧 Configuration

### Model
Edit `backend/chat/rag.py` line ~39:
```python
self.llm = ChatOpenAI(model="gpt-4o-mini")  # Change model here
```

### RAG Parameters
Edit `backend/chat/rag.py`:
- Chunk size: line 53
- Chunk overlap: line 54
- Retrieval k: line 61
- Temperature: line 39

### API Endpoint (Production)
Edit `frontend/.env`:
```
VITE_API_URL=https://your-domain.com/api
```

---

## 📍 API Endpoints

### Send Message
```bash
POST /api/chat/
Content-Type: application/json

{
  "session_id": "optional-uuid",
  "user_message": "Your question"
}
```

### Get Session
```bash
GET /api/session/{session_id}/
```

### Create Session
```bash
POST /api/session/
```

---

## 🆚 Ports

| Component | Port | URL |
|-----------|------|-----|
| Backend (Django) | 8000 | http://localhost:8000 |
| Frontend (Vite) | 5173 | http://localhost:5173 |
| API | 8000 | http://localhost:8000/api |

---

## 🐛 Common Issues & Quick Fixes

| Issue | Fix |
|-------|-----|
| "ModuleNotFoundError" | `pip install -r requirements.txt` |
| "OPENAI_API_KEY not found" | Edit `backend/.env` and add key |
| "Connection refused" | Make sure both servers running |
| "Port in use" | Kill process: `lsof -i :8000` |
| "PDFs not loading" | Restart backend after adding PDFs |
| "Generic AI response" | Add PDFs to `knowledge_base/` |

---

## ✅ Validation Steps

1. Backend running? → Visit `http://localhost:8000/api/session/`
2. Frontend running? → Visit `http://localhost:5173`
3. Chat working? → Send message and wait for response
4. Sources showing? → Add PDFs and ask about them
5. History persisting? → Refresh page and check messages

---

## 📦 Add Sample Data

```bash
cd backend
pip install reportlab
python generate_sample_pdfs.py
# Restart backend
python manage.py runserver
```

---

## 🚀 Deploy (Production)

1. Set `DEBUG=False` in `settings.py`
2. Update `ALLOWED_HOSTS`
3. Switch to PostgreSQL
4. Use Gunicorn/uWSGI
5. Setup HTTPS/SSL
6. Deploy backend
7. Build frontend: `npm run build`
8. Deploy `dist/` folder

---

## 📚 Documentation

| Document | Purpose | Read Time |
|----------|---------|-----------|
| `INDEX.md` | Navigation guide | 5 min |
| `QUICK_START.md` | Fast setup | 5 min |
| `README.md` | Full docs | 30 min |
| `ARCHITECTURE.md` | System design | 20 min |
| `TROUBLESHOOTING.md` | Fix issues | 30 min |
| `ENVIRONMENT_SETUP.md` | API key setup | 15 min |
| `IMPLEMENTATION_SUMMARY.md` | What was built | 15 min |

---

## 🎯 Common Tasks

### Change AI Model
```python
# In backend/chat/rag.py line 39
# Options: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
self.llm = ChatOpenAI(model="gpt-4o-mini")
```

### Adjust Response Creativity
```python
# In backend/chat/rag.py line 39
# 0.0 = deterministic, 1.0 = creative
self.llm = ChatOpenAI(temperature=0.7)
```

### Get More Context from Documents
```python
# In backend/chat/rag.py line 61
# k = number of documents to retrieve
search_kwargs={"k": 5}  # Get 5 instead of 3
```

### Use Bulk PDFs
1. Place PDF files in `backend/knowledge_base/`
2. Restart Django server
3. System loads automatically

### Customize Chat UI
Edit CSS files in `frontend/src/styles/`:
- `ChatContainer.css` - Main layout
- `MessageBubble.css` - Message styling
- `MessageInput.css` - Input styling
- `SourceCitation.css` - Sources styling

---

## 🧪 Test API Manually

```bash
# Create session
curl -X POST http://localhost:8000/api/session/

# Send message (replace session_id)
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"user_message":"Hello"}'

# Get session history
curl http://localhost:8000/api/session/YOUR_SESSION_ID/
```

---

## 💰 Cost Tips

- Use `gpt-3.5-turbo` for cheaper responses
- Smaller chunk sizes = fewer tokens
- Reduce retrieval count: `k=1` or `k=2`
- Cache common questions
- Monitor at: https://platform.openai.com/account/usage

---

## 🔒 Security Checklist

- [x] API key in `.env` (not in code)
- [x] `.env` in `.gitignore`
- [x] CORS configured
- [x] Validate all inputs
- ⚠️ Add authentication before production
- ⚠️ Use HTTPS in production
- ⚠️ Set rate limits

---

## 📊 Performance Notes

- First response: 3-5 sec (embedding + generation)
- Subsequent: 2-3 sec
- With large docs: 5-10 sec
- FAISS search: < 10ms
- Database query: < 50ms

---

## 🎓 Learning Resources

### Understanding RAG
- LangChain docs: https://python.langchain.com
- FAISS docs: https://faiss.ai
- OpenAI docs: https://platform.openai.com/docs

### Django
- Django docs: https://docs.djangoproject.com
- DRF docs: https://www.django-rest-framework.org

### React
- React docs: https://react.dev
- Vite docs: https://vitejs.dev

---

## 🆘 Get Help

1. Check `TROUBLESHOOTING.md`
2. Read `README.md` for your issue
3. Review `ARCHITECTURE.md` for system design
4. Check browser console (F12)
5. Check backend terminal output

---

## 📋 Setup Checklist

- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed
- [ ] OpenAI API key obtained
- [ ] Backend dependencies installed
- [ ] Database migrations run
- [ ] `.env` file created with API key
- [ ] Frontend dependencies installed
- [ ] Backend running on :8000
- [ ] Frontend running on :5173
- [ ] Chat UI loads in browser
- [ ] Can send test message
- [ ] Get response with sources

**All checked?** ✅ You're ready to demo!

---

## 🎉 You're All Set!

```bash
# Quick start
setup.bat              # or setup.sh on macOS/Linux

# Or manual
python manage.py runserver  # Backend
npm run dev                 # Frontend (new terminal)

# Open browser
http://localhost:5173

# Start chatting!
```

---

## 📞 Quick Links

- [Start Here](QUICK_START.md) - 10 min setup
- [API Key Setup](ENVIRONMENT_SETUP.md) - Get started
- [Full Docs](README.md) - Everything
- [Fix Issues](TROUBLESHOOTING.md) - Troubleshooting
- [System Design](ARCHITECTURE.md) - How it works
- [Navigation](INDEX.md) - Find anything

---

**Questions?** See [INDEX.md](INDEX.md) for a complete documentation index!

**Ready?** Open [QUICK_START.md](QUICK_START.md) and get started! 🚀
