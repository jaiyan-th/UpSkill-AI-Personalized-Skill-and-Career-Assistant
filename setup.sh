#!/bin/bash

# UpSkill AI Setup Script
# This script automates the setup process for UpSkill AI

echo "🚀 UpSkill AI Setup Script"
echo "=========================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Navigate to backend directory
cd backend || exit

echo "📦 Setting up backend..."
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit backend/.env and add your Groq API key!"
    echo "   Get your API key from: https://console.groq.com"
    echo ""
fi

# Initialize database
echo "Initializing database..."
python setup.py

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit backend/.env and add your GROQ_API_KEY"
echo "   2. Start the backend: cd backend && python run.py"
echo "   3. Start the frontend: cd frontend && python server.py"
echo "   4. Open http://localhost:5174 in your browser"
echo ""
echo "🎉 Happy coding!"
