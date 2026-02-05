#!/bin/bash

# Virtual Try-On Application Startup Script
# This script starts both the backend (FastAPI) and frontend (React/Vite) servers

echo "🚀 Starting Virtual Try-On Application..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the titan directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}Error: Please run this script from the titan project root directory${NC}"
    exit 1
fi

# Function to kill background processes on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup INT TERM

# 1. Start Backend
echo -e "${GREEN}[1/2] Starting Backend (FastAPI)...${NC}"
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.dependencies_installed" ]; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r requirements.txt
    touch venv/.dependencies_installed
fi

# Start backend server
echo -e "${GREEN}Backend starting on http://localhost:8000${NC}"
uvicorn app.main:app --reload &
BACKEND_PID=$!

cd ..

# 2. Start Frontend
echo -e "${GREEN}[2/2] Starting Frontend (React + Vite)...${NC}"
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install
fi

# Start frontend server
echo -e "${GREEN}Frontend starting on http://localhost:5173${NC}"
npm run dev &
FRONTEND_PID=$!

cd ..

# Wait a bit for servers to start
sleep 3

echo ""
echo -e "${GREEN}✅ Application is running!${NC}"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Wait for background processes
wait
