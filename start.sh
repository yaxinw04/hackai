#!/bin/bash

# YouTube to Shorts - Start All Services
# Run this script from the root directory: ./start.sh

set -e  # Exit on any error

echo "🚀 Starting YouTube to Shorts Services..."
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to cleanup background processes
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    
    # Kill backend if it's running
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${BLUE}   Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Kill frontend if it's running
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${BLUE}   Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ All services stopped.${NC}"
    exit 0
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGINT SIGTERM

# Check if required directories exist
if [ ! -d "backend" ]; then
    echo -e "${RED}❌ Backend directory not found!${NC}"
    echo "Make sure you're running this from the project root directory."
    exit 1
fi

if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Frontend directory not found!${NC}"
    echo "Make sure you're running this from the project root directory."
    exit 1
fi

# Clean up any junk files from pip command typos
if find . -name "=*" -type f -print -quit | grep -q "="; then
    echo -e "${YELLOW}🧹 Cleaning up junk files from pip command typos...${NC}"
    find . -name "=*" -type f -delete
    echo -e "${GREEN}   ✅ Cleaned up junk files${NC}"
fi

# Install dependencies if needed
echo -e "${YELLOW}📦 Checking dependencies...${NC}"

# Check backend dependencies
if [ ! -f "backend/venv/bin/activate" ]; then
    echo -e "${BLUE}   Setting up backend virtual environment...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
    cd ..
else
    echo -e "${GREEN}   ✅ Backend virtual environment exists${NC}"
fi

# Check frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${BLUE}   Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd ..
else
    echo -e "${GREEN}   ✅ Frontend dependencies installed${NC}"
fi

echo ""
echo -e "${YELLOW}🔧 Starting services...${NC}"

# Start Backend
echo -e "${BLUE}   Starting backend server...${NC}"
cd backend
source venv/bin/activate

# Set environment variables to force system FFmpeg usage (avoid Santa restrictions)
export USE_SYSTEM_FFMPEG=1
export IMAGEIO_FFMPEG_EXE=$(which ffmpeg 2>/dev/null || echo "")
if [ -n "$IMAGEIO_FFMPEG_EXE" ]; then
    echo -e "${GREEN}   🎬 Using system FFmpeg: $IMAGEIO_FFMPEG_EXE${NC}"
else
    echo -e "${YELLOW}   ⚠️  System FFmpeg not found, may fall back to bundled version${NC}"
fi

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}   ✅ Backend started (PID: $BACKEND_PID)${NC}"
    echo -e "${GREEN}   📡 Backend running at: http://localhost:8000${NC}"
    echo -e "${GREEN}   📖 API docs at: http://localhost:8000/docs${NC}"
else
    echo -e "${RED}   ❌ Backend failed to start${NC}"
    echo "Check backend.log for errors:"
    cat backend.log
    exit 1
fi

# Start Frontend
echo -e "${BLUE}   Starting frontend server...${NC}"
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 3

# Check if frontend started successfully
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}   ✅ Frontend started (PID: $FRONTEND_PID)${NC}"
    echo -e "${GREEN}   🌐 Frontend running at: http://localhost:3000${NC}"
else
    echo -e "${RED}   ❌ Frontend failed to start${NC}"
    echo "Check frontend.log for errors:"
    cat frontend.log
    cleanup
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All services are running!${NC}"
echo "==============================================="
echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}API Docs: http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}💡 Logs are being written to:${NC}"
echo -e "   Backend: backend.log"
echo -e "   Frontend: frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep the script running and show live logs
echo -e "${BLUE}📋 Live logs (Ctrl+C to stop):${NC}"
echo "==============================================="

# Follow both log files
tail -f backend.log frontend.log 2>/dev/null &
TAIL_PID=$!

# Wait for user to press Ctrl+C
wait $TAIL_PID 2>/dev/null || cleanup 