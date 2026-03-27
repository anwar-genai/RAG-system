# Environment Setup Guide

## Getting Your OpenAI API Key

### Step 1: Create an OpenAI Account

1. Go to https://openai.com
2. Click "Sign up" or "Log in" if you have an account
3. Complete the signup process
4. Verify your email

### Step 2: Get Your API Key

1. Go to https://platform.openai.com/account/api-keys
2. Click "Create new secret key"
3. Give it a name (e.g., "RAG Chat System")
4. Click "Create secret key"
5. **Copy the entire key** - it will only be shown once!

⚠️ **Important**: Never share your API key or commit it to version control!

### Step 3: Set Up the .env File

#### Option A: Using the setup script (Automatic)

Run the setup script (`setup.bat` on Windows or `setup.sh` on macOS/Linux).
It will create `.env` from `.env.example`.

#### Option B: Manual Setup

1. Navigate to the `backend` folder
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

3. Open `backend/.env` in a text editor
4. Find the line: `OPENAI_API_KEY=your-openai-api-key-here`
5. Replace it with your actual API key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here-1234567890abcdef
   ```

6. Save the file

## Backend Environment Variables

The `.env` file in the backend should contain:

```bash
# Required: Your OpenAI API key
OPENAI_API_KEY=sk-...

# Django settings (can be left as default)
SECRET_KEY=django-insecure-... 
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite by default)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

## Frontend Environment Variables

The `.env` file in the frontend is pre-configured:

```bash
VITE_API_URL=/api
```

This tells the frontend where to find the API. During development, Vite's proxy will forward requests to `http://localhost:8000`.

### For Production

If deploying to production, change `VITE_API_URL` to your actual backend URL:

```bash
VITE_API_URL=https://your-domain.com/api
```

## Model Selection

The system uses `gpt-4o-mini` by default, which is:
- ✅ Cost-effective
- ✅ Fast
- ✅ High quality for most use cases

### To use a different model:

Edit `backend/chat/rag.py` and change:

```python
self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
```

Available models (check current availability):
- `gpt-4o` - Most capable
- `gpt-4o-mini` - Fast and cheap (recommended)
- `gpt-4-turbo` - Good balance
- `gpt-3.5-turbo` - Budget option

## API Key Security Best Practices

### ✅ DO:
- Store API keys in `.env` files (never in code)
- Use a `.gitignore` file to exclude `.env` from version control
- Rotate keys regularly
- Define permissions/limit key usage in OpenAI dashboard
- Use different keys for development/production

### ❌ DON'T:
- Commit `.env` to Git
- Share API keys in emails or chat
- Display API keys in error messages
- Use the same key for multiple projects
- Hardcode API keys in source code

## Checking Your Setup

### Test Backend Connection:

```bash
cd backend
python -c "from langchain_openai import ChatOpenAI; print('✓ OpenAI imports working')"
```

### Test API Key:

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); import openai; print('✓ API key loaded')"
```

### Check Required Packages:

```bash
pip list | grep -E "django|langchain|openai|faiss"
```

## Troubleshooting

### "OpenAIAPIError: Incorrect API key provided"

**Solution**: 
1. Double-check your API key in `.env`
2. Make sure it starts with `sk-`
3. Verify it has no extra spaces: `OPENAI_API_KEY=sk-xxx` (not `OPENAI_API_KEY= sk-xxx `)
4. Check your API key is active at https://platform.openai.com/account/api-keys

### "RateLimitError: 429"

**Solution**: You've exceeded your rate limit. Either:
1. Wait a bit and try again
2. Use a different key or account
3. Upgrade your OpenAI plan

### "No module named 'openai'"

**Solution**: Install the package:
```bash
pip install openai langchain-openai
```

### "OPENAI_API_KEY not found"

**Solution**:
1. Make sure `.env` exists in the `backend` directory
2. Make sure the file has the line with your key
3. Restart the Django server after editing `.env`
4. Verify the `.env` file is not in `.gitignore`

## Getting API Costs

### Pricing Overview

- **Input tokens**: Usually cheaper per 1M tokens
- **Output tokens**: Usually 2x-3x more expensive per 1M tokens

Example costs (as of Feb 2026):
- `gpt-4o-mini`: ~$0.15-0.60 per 1M tokens
- `gpt-4o`: ~$5-15 per 1M tokens

### Free Trial API Credits

New OpenAI accounts get ~$5-10 free credits that expire in 3 months.

### Track Usage

1. Go to https://platform.openai.com/account/usage/overview
2. View your usage in real-time
3. Set up billing alerts to avoid surprises

### Tips to Save Money

1. Use `gpt-3.5-turbo` for simple queries (cheapest)
2. Reduce context window size in `rag.py` (fewer tokens)
3. Cache commonly asked questions
4. Use smaller models for document embedding (already optimized)

---

**You're ready to use the OpenAI API!** 🚀
