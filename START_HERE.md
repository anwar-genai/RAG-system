# 🚀 START HERE

Welcome! You have a complete RAG-based AI chat system ready to run.

---

## ⏱️ Quick Start (Choose One)

### Option 1: Automatic Setup (Easiest - 2 minutes) ✅ RECOMMENDED

**Windows:**
```bash
setup.bat
```

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

Then follow the on-screen instructions.

### Option 2: Manual Setup (10 minutes)

Follow: [QUICK_START.md](QUICK_START.md)

---

## 🔑 One Important Step

**Before running, you need:**
1. Get OpenAI API key: https://platform.openai.com/account/api-keys
2. Edit `backend/.env` and add it there
3. That's it!

See: [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) for detailed help

---

## ✅ Then What?

After setup:
1. Backend runs at `http://localhost:8000`
2. Frontend runs at `http://localhost:5173`
3. Open browser to `http://localhost:5173`
4. Start chatting!

---

## 📚 Documentation Map

| Need | Read |
|------|------|
| Setup | [QUICK_START.md](QUICK_START.md) |
| API Key Help | [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) |
| Full Docs | [README.md](README.md) |
| How It Works | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Issues? | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Navigation | [INDEX.md](INDEX.md) |
| Reference | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |

---

## 🎯 Popular Questions

**Q: How long does setup take?**
A: 10 minutes with the quick start, or 2 minutes with the setup script.

**Q: Where do I add my API key?**
A: Edit `backend/.env` - See [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)

**Q: How do I add PDFs?**
A: Put them in `backend/knowledge_base/` and restart the backend.

**Q: Can I customize it?**
A: Yes! UI colors, model choice, RAG parameters - all explained in docs.

**Q: Can I deploy it?**
A: Yes! See [README.md](README.md#production-deployment)

---

## 🚨 If Something Goes Wrong

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Run the verification in that guide
3. Check browser console (F12)
4. Check backend terminal output

---

## 🎓 What's Included

✅ Full-stack RAG chat system (Backend + Frontend)
✅ LangChain + FAISS + OpenAI integration
✅ ChatGPT-style UI
✅ Complete documentation
✅ Setup scripts
✅ Sample data generator
✅ Production-ready code

---

## 🎯 Ready?

### Step 1: Setup (Choose One)

Windows: Run `setup.bat`
macOS/Linux: Run `setup.sh`
Other: Follow [QUICK_START.md](QUICK_START.md)

### Step 2: Add API Key

Edit `backend/.env` with your OpenAI API key

### Step 3: Start Servers

```bash
# Backend (Terminal 1)
cd backend
python manage.py runserver

# Frontend (Terminal 2)
cd frontend
npm run dev
```

### Step 4: Chat!

Open `http://localhost:5173` in your browser

---

## 📱 System Requirements

✅ Python 3.9+
✅ Node.js 16+
✅ npm
✅ OpenAI API key
✅ ~500MB disk space

---

## 🔒 Security First

Your API key goes in `backend/.env` - never commits to git.

See: [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md#api-key-security-best-practices)

---

## 💰 Costs

Mainly OpenAI API usage (cheap with gpt-4o-mini).
See: [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md#getting-api-costs)

---

## ✨ Examples

### Pre-Made to Run Immediately
```bash
# No PDFs needed - works with demo data
# Just setup and chat!
```

### With Sample Data
```bash
# Optional - generate sample PDFs for testing
cd backend
python generate_sample_pdfs.py
```

### With Your PDFs
```bash
# Put any PDF in backend/knowledge_base/
# Restart backend
# Chat about them!
```

---

## 📞 Need Help?

1. **First time?** → [QUICK_START.md](QUICK_START.md)
2. **Getting errors?** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. **Want to learn?** → [ARCHITECTURE.md](ARCHITECTURE.md)
4. **Find anything?** → [INDEX.md](INDEX.md)

---

## 🎉 That's It!

You have everything you need to:
- Run it locally
- Customize it
- Deploy it
- Show clients
- Build on it

---

## ➡️ NEXT STEPS

### Pick One:

**I'm ready to start now:**
→ Run `setup.bat` (Windows) or `setup.sh` (macOS/Linux)

**I want step-by-step guide:**
→ Open [QUICK_START.md](QUICK_START.md)

**I need to add my API key:**
→ Open [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)

**I want to understand it first:**
→ Open [README.md](README.md)

---

**Let's go! 🚀**

Choose one of the options above and get started in minutes.

Questions? See [INDEX.md](INDEX.md) for complete navigation.
