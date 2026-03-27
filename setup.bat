@echo off
REM Quick start script for RAG Chat System on Windows

echo.
echo ========================================
echo RAG Chat System - Backend Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/6] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/6] Installing dependencies...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/6] Checking for .env file...
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo *** IMPORTANT: Edit backend\.env and add your OpenAI API key! ***
    echo Get your key from: https://platform.openai.com/account/api-keys
    echo.
)

echo [5/6] Running database migrations...
python manage.py makemigrations
python manage.py migrate
if %errorlevel% neq 0 (
    echo Error: Database migrations failed
    pause
    exit /b 1
)

echo [6/6] Setup complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Edit backend\.env and add your OpenAI API key
echo.
echo 2. Start the backend server:
echo    python manage.py runserver
echo.
echo 3. In a new terminal, install frontend dependencies:
echo    cd frontend
echo    npm install
echo.
echo 4. Start the frontend server:
echo    npm run dev
echo.
echo 5. Open http://localhost:5173 in your browser
echo.
echo 6. (Optional) Add PDF files to backend/knowledge_base/
echo.
pause
