@echo off
REM UpSkill AI Setup Script for Windows
REM This script automates the setup process for UpSkill AI

echo.
echo ========================================
echo    UpSkill AI Setup Script (Windows)
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Navigate to backend directory
cd backend
if errorlevel 1 (
    echo [ERROR] Backend directory not found
    pause
    exit /b 1
)

echo [STEP 1] Setting up backend...
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo.
    echo [WARNING] .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo [IMPORTANT] Please edit backend\.env and add your Groq API key!
    echo Get your API key from: https://console.groq.com
    echo.
)

REM Initialize database
echo Initializing database...
python setup.py
if errorlevel 1 (
    echo [ERROR] Failed to initialize database
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit backend\.env and add your GROQ_API_KEY
echo   2. Start the backend: cd backend ^&^& python run.py
echo   3. Start the frontend: cd frontend ^&^& python server.py
echo   4. Open http://localhost:5174 in your browser
echo.
echo Happy coding!
echo.
pause
