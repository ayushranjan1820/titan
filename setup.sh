#!/bin/bash

# Setup script for the Virtual Try-On POC
# This script sets up both backend and frontend

echo "========================================="
echo "Virtual Try-On POC - Setup Script"
echo "========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

echo "✅ Node.js found: $(node --version)"
echo ""

# ========================================
# Backend Setup
# ========================================

echo "📦 Setting up Backend..."
echo ""

cd backend || exit

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Backend setup complete!"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env and add your LLM API key (OPENAI_API_KEY or GOOGLE_API_KEY)"
fi

cd ..

# ========================================
# Frontend Setup
# ========================================

echo "📦 Setting up Frontend..."
echo ""

cd frontend || exit

# Install npm dependencies
echo "Installing npm dependencies..."
npm install

echo "✅ Frontend setup complete!"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

cd ..

# ========================================
# Scraper Setup
# ========================================

echo "📦 Setting up Scraper..."
echo ""

cd scraper || exit

# Install scraper dependencies (in same venv as backend)
source ../backend/venv/bin/activate
pip install -r requirements.txt

echo "✅ Scraper setup complete!"
echo ""

cd ..

# ========================================
# Create data directory
# ========================================

mkdir -p data

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. (Optional) Run the scraper to collect product data:"
echo "   cd scraper"
echo "   source ../backend/venv/bin/activate"
echo "   python src/run_scraper.py --config config/watches_site_template.yaml --limit 100"
echo ""
echo "2. Start the backend API:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "3. Start the frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. Open http://localhost:5173 in your browser"
echo ""
echo "⚠️  Don't forget to set your LLM API key in backend/.env!"
echo ""
