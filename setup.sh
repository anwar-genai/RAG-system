#!/bin/bash

# Quick start script for RAG Chat System on macOS/Linux

echo ""
echo "========================================"
echo "RAG Chat System - Backend Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

echo "[1/6] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

echo "[2/6] Activating virtual environment..."
source venv/bin/activate

echo "[3/6] Installing dependencies..."
cd backend
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo "[4/6] Checking for .env file..."
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "*** IMPORTANT: Edit backend/.env and add your OpenAI API key! ***"
    echo "Get your key from: https://platform.openai.com/account/api-keys"
    echo ""
fi

echo "[5/6] Running database migrations..."
python manage.py makemigrations
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "Error: Database migrations failed"
    exit 1
fi

echo "[6/6] Setup complete!"
echo ""
echo "========================================"
echo "Next Steps:"
echo "========================================"
echo ""
echo "1. Edit backend/.env and add your OpenAI API key"
echo ""
echo "2. Start the backend server:"
echo "   python manage.py runserver"
echo ""
echo "3. In a new terminal, install frontend dependencies:"
echo "   cd frontend"
echo "   npm install"
echo ""
echo "4. Start the frontend server:"
echo "   npm run dev"
echo ""
echo "5. Open http://localhost:5173 in your browser"
echo ""
echo "6. (Optional) Add PDF files to backend/knowledge_base/"
echo ""
