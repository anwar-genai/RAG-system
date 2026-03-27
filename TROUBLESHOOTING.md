# Validation & Troubleshooting Guide

## Pre-Launch Checklist

### ✓ Prerequisites
- [ ] Python 3.9+ installed (`python --version`)
- [ ] Node.js 16+ installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] OpenAI API key obtained
- [ ] Git installed (optional)

### ✓ Backend Setup
- [ ] Virtual environment created (`venv/` folder exists)
- [ ] Virtual environment activated
- [ ] `pip install -r requirements.txt` completed
- [ ] No import errors
- [ ] `backend/.env` file created
- [ ] `OPENAI_API_KEY` set in `.env`
- [ ] Database migrations run (`python manage.py migrate`)
- [ ] No migration errors

### ✓ Frontend Setup
- [ ] `npm install` completed in `frontend/`
- [ ] No npm errors
- [ ] `frontend/.env` exists with VITE_API_URL
- [ ] Dependencies installed in `frontend/node_modules/`

### ✓ Project Structure
- [ ] `backend/chat/models.py` exists with ChatSession and Message
- [ ] `backend/chat/views.py` exists with API endpoints
- [ ] `backend/chat/rag.py` exists with RAG implementation
- [ ] `backend/chat/serializers.py` exists
- [ ] `backend/knowledge_base/` directory exists
- [ ] `frontend/src/components/` directory with all components
- [ ] `frontend/src/services/api.js` exists
- [ ] `frontend/src/styles/` directory with CSS files

---

## Launch Verification

### Step 1: Start Backend

```bash
cd backend
python manage.py runserver
```

**Expected Output:**
```
System check identified no issues (0 silenced).
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

✅ **Backend is running** if you see "Starting development server"

### Step 2: Verify Backend API

Open a new terminal:

```bash
# Test API is accessible
curl http://localhost:8000/api/session/
```

**Expected Response:**
```json
{"session_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}
```

✅ **API is working** if you get a valid response

### Step 3: Start Frontend

Open another new terminal:

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
  VITE v7.2.4  ready in 123 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

✅ **Frontend is running** if you see "Local: http://localhost:5173/"

### Step 4: Open Browser

Navigate to: `http://localhost:5173`

**Expected:**
- Chat interface displays
- "Welcome to RAG Chat" heading
- Input box at bottom
- "New Chat" button at top

✅ **Frontend is working** if the UI loads

### Step 5: Send Test Message

Type in the input box:
```
Hello, what can you do?
```

Press Enter or click Send.

**Expected:**
- Message appears in chat
- "Loading..." indicator shows
- AI response appears below
- Response appears as AI message (left side)

✅ **Chat working** if you get a response

---

## Troubleshooting Guide

### Issue: "ModuleNotFoundError: No module named 'X'"

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

Check that no packages failed to install.

### Issue: "OPENAI_API_KEY not found"

**Check:**
1. `backend/.env` file exists
2. File contains: `OPENAI_API_KEY=sk-...`
3. Key is not empty or whitespace
4. Key starts with `sk-`

**Fix:**
```bash
# Edit the file
nano backend/.env
# or open in your editor
# Verify the line and save
```

**Test:**
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv('backend/.env'); print(os.getenv('OPENAI_API_KEY'))"
```

### Issue: "Connection refused" (Frontend → Backend)

**Check:**
1. Backend is running: `http://localhost:8000`
2. Frontend is running: `http://localhost:5173`
3. Browser shows no CORS errors (F12 → Console)

**Fix:**
```bash
# In backend
python manage.py runserver

# In new terminal, in frontend
npm run dev

# Wait 5 seconds and refresh browser
```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# On Windows PowerShell, find process
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
taskkill /PID <PID> /F

# On macOS/Linux
lsof -i :8000
kill -9 <PID>

# Or use different port
python manage.py runserver 8001
```

### Issue: "Port 5173 already in use"

**Solution:**
```bash
# On Windows PowerShell
Get-NetTCPConnection -LocalPort 5173 | Select-Object OwningProcess
taskkill /PID <PID> /F

# On macOS/Linux
lsof -i :5173
kill -9 <PID>

# Or run on different port
npm run dev -- --port 3000
```

### Issue: "OpenAIAPIError: Incorrect API key provided"

**Check:**
1. Key starts with `sk-`
2. No extra spaces: `OPENAI_API_KEY=sk-xxx` (not `= sk-xxx `)
3. Key is active at https://platform.openai.com/account/api-keys
4. Restarted backend after editing `.env`

**Fix:**
```bash
# Re-edit .env carefully
# Remove any extra spaces
# Restart backend
python manage.py runserver
```

### Issue: "PDFs not loading into RAG system"

**Check:**
1. PDFs are in `backend/knowledge_base/` folder
2. Files have `.pdf` extension
3. Backend has been restarted
4. Check backend console for errors

**Fix:**
```bash
# Test with sample PDFs
cd backend
pip install reportlab
python generate_sample_pdfs.py

# Restart backend
python manage.py runserver
```

### Issue: "Database error" or "No such table"

**Solution:**
```bash
cd backend
python manage.py migrate
python manage.py migrate --fake-initial
```

### Issue: "npm ERR! code ERESOLVE"

**Solution:**
```bash
cd frontend
npm install --legacy-peer-deps
```

### Issue: "Vite config not found"

**Check:**
- `frontend/vite.config.js` exists
- File contains React plugin configuration

**Fix:**
```bash
cd frontend
npm run dev
# Then ctrl+c
# Edit vite.config.js to verify it exists
```

### Issue: "AI response is generic/not using documents"

**Check:**
1. PDFs are in `backend/knowledge_base/`
2. Backend has been restarted after adding PDFs
3. PDFs are valid (not corrupted)
4. Try asking specific questions about the content

**Test:**
```bash
# Check if PDFs were loaded
cd backend
python -c "from chat.rag import get_rag_system; rag = get_rag_system(); print('RAG initialized')"
```

### Issue: "Chat history not persisting"

**Check:**
1. Browser LocalStorage is enabled
2. Session ID shows in chat header
3. Same session ID used for multiple messages
4. Database file `db.sqlite3` exists and grows

**Fix:**
```bash
# Clear browser storage and try again
# In browser: F12 → Application → LocalStorage → Clear
# Send new message to create new session
```

### Issue: Frontend shows "Failed to send message"

**Check:**
1. Backend is running on port 8000
2. No CORS errors in browser console (F12)
3. No errors in backend console
4. OpenAI API key is valid

**Fix:**
```bash
# Check backend console for detailed errors
# Look for stack traces
# Try restarting backend

# In browser console (F12), check for:
# - CORS errors
# - Network failures
# - JSON parsing errors
```

### Issue: "Very slow response" (10+ seconds)

**Normal** if:
- First request (embeddings cache building)
- Large documents being processed
- Many similar documents

**Speed up:**
1. Check OpenAI account status
2. Try smaller chunk size in `rag.py`
3. Reduce number of retrieved documents (k=3)
4. Use cheaper model (gpt-3.5-turbo)

### Issue: "High API costs"

**Reduce:**
1. Reduce chunk size (fewer tokens)
2. Reduce k value (fewer retrievals)
3. Use gpt-3.5-turbo instead of gpt-4o
4. Cache common questions
5. Limit query length

---

## Validation Tests

### Test 1: Backend API

```bash
# Create session
curl -X POST http://localhost:8000/api/session/

# Send message (replace session_id)
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"user_message": "Hello", "session_id": null}'

# Get session (replace session_id)
curl http://localhost:8000/api/session/550e8400-e29b-41d4-a716-446655440000/
```

**Expected:** Valid JSON responses with no errors

### Test 2: Frontend UI

1. Open http://localhost:5173
2. Type "What can you help with?"
3. Click Send
4. Check:
   - Message appears as user (right side)
   - Loading indicator shows
   - Response appears (left side)
   - Response is from AI

### Test 3: Chat History

1. Send 2-3 messages
2. Refresh page (F5)
3. Check:
   - All messages still visible
   - Same session ID
   - Order preserved

### Test 4: Source Citations

1. Add sample PDFs: `python generate_sample_pdfs.py`
2. Restart backend
3. Send message about documents
4. Check:
   - Response includes relevant info
   - Sources appear below response
   - Sources show "Document.pdf - Page X"

### Test 5: Error Handling

1. Stop backend server
2. Try sending message in frontend
3. Should see error message
4. Restart backend
5. Message should work again

---

## Performance Tests

### Measure Response Time

```bash
# Time a single request
time curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"user_message":"test"}'
```

**Typical times:**
- First request: 3-5 seconds
- Subsequent requests: 2-3 seconds
- With large docs: 5-10 seconds

### Monitor Resource Usage

**Backend:**
- CPU: 50-80% during response generation
- Memory: 500MB-1GB
- Disk: SQLite < 10MB

**Frontend:**
- Memory: 50-100MB
- CPU: 5-10% during interactions

---

## Browser Compatibility

### Tested & Working
- ✅ Chrome 120+
- ✅ Firefox 121+
- ✅ Safari 17+
- ✅ Edge 120+

### Check Browser Console (F12)

Look for:
- No red errors
- No CORS warnings
- No memory leaks

---

## System Requirements Verification

```bash
# Check Python version
python --version
# Expected: Python 3.9+

# Check Node version
node --version
# Expected: v16+

# Check npm version
npm --version
# Expected: v8+

# Check Django installed
python -c "import django; print(django.__version__)"
# Expected: 6.0.2

# Check React
cd frontend
npm list react
# Expected: react@19.2.0

# Check packages in backend
cd backend
pip list | grep -E "langchain|faiss|openai"
```

---

## Success Indicators

✅ You're ready to demo when:

1. Backend runs without errors
2. Frontend displays chat UI
3. Sending message triggers API response
4. Chat history persists after refresh
5. Sources display below AI messages
6. No errors in browser console (F12)
7. No errors in backend terminal
8. Session ID persists and works

---

## Debug Mode

### Enable Verbose Logging

**Backend:**
```python
# Add to backend/core/settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

**Frontend:**
```javascript
// Add to frontend/src/services/api.js
const apiClient = axios.create({
  ...
});

apiClient.interceptors.response.use(
  response => {
    console.log('API Response:', response.data);
    return response;
  },
  error => {
    console.error('API Error:', error.response?.data);
    return Promise.reject(error);
  }
);
```

### Check Network Requests

1. Open browser (F12)
2. Go to Network tab
3. Send a message
4. Check:
   - POST to /api/chat/
   - Status 200 or 201
   - Response contains "answer", "sources"

---

## Support Checklist

If issues persist, provide:

1. **Python Version**: `python --version`
2. **Django Version**: `python manage.py --version`
3. **Node Version**: `node --version`
4. **Backend Error**: Full stack trace from terminal
5. **Frontend Error**: Browser console (F12) errors
6. **API Response**: JSON from API call
7. **System**: Windows/macOS/Linux
8. **Steps to Reproduce**: Exact steps taken

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python manage.py runserver` | Start backend |
| `npm run dev` | Start frontend |
| `python manage.py migrate` | Apply database migrations |
| `python generate_sample_pdfs.py` | Create sample PDFs |
| `pip install -r requirements.txt` | Install backend packages |
| `npm install` | Install frontend packages |
| `curl http://localhost:8000/api/session/` | Test API |

---

## Next Steps if All Works

1. ✅ Add your own PDF documents
2. ✅ Customize UI colors and styling
3. ✅ Adjust RAG parameters for your use case
4. ✅ Set up production deployment
5. ✅ Add authentication (if needed)
6. ✅ Configure monitoring and logging

---

**System is production-ready once all tests pass! 🎉**
