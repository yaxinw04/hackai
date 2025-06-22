#!/bin/bash

# YouTube to Shorts - Complete Setup Script
# Run this script from the project root directory: ./setup.sh

set -e  # Exit on any error

# Check for --python311 flag
USE_PYTHON311=false
if [ "$1" = "--python311" ]; then
    USE_PYTHON311=true
    echo "🐍 Using Python 3.11 mode"
fi

echo "🔧 YouTube to Shorts - Complete Setup"
echo "======================================"

# Quick Python version check upfront
if command -v python3 >/dev/null 2>&1; then
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    python_minor=$(echo $python_version | cut -d'.' -f2)
    if [ "$(echo $python_version | cut -d'.' -f1)" -eq 3 ] && [ "$python_minor" -ge 13 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Python 3.13+ Compatibility Warning${NC}"
        echo -e "${YELLOW}Your system has Python $python_version, which may cause issues with AI/ML packages.${NC}"
        echo -e "${YELLOW}For best results, consider using Python 3.11 or 3.12.${NC}"
        echo ""
        echo -e "${BLUE}Quick fix: Install Python 3.11 with: ${GREEN}brew install python@3.11${NC}"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Exiting. Install Python 3.11 and try again.${NC}"
            exit 0
        fi
        echo ""
    fi
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        python_major=$(echo $python_version | cut -d'.' -f1)
        python_minor=$(echo $python_version | cut -d'.' -f2)
        
        # Check if Python version is too new (3.13+)
        if [ "$python_major" -eq 3 ] && [ "$python_minor" -ge 13 ]; then
            echo -e "${YELLOW}   ⚠️  Python $python_version found (may have compatibility issues)${NC}"
            echo -e "${YELLOW}   Some AI/ML packages (like openai-whisper) don't support Python 3.13+ yet${NC}"
            echo -e "${YELLOW}   Consider using Python 3.11 or 3.12 for better compatibility${NC}"
            return 2  # Warning, but continue
        elif [ "$python_major" -eq 3 ] && [ "$python_minor" -ge 8 ]; then
            echo -e "${GREEN}   ✅ Python $python_version found${NC}"
            return 0
        else
            echo -e "${RED}   ❌ Python $python_version found (requires Python 3.8+)${NC}"
            return 1
        fi
    else
        echo -e "${RED}   ❌ Python3 not found${NC}"
        return 1
    fi
}

# Function to check Node.js version
check_node_version() {
    if command_exists node; then
        node_version=$(node --version)
        echo -e "${GREEN}   ✅ Node.js $node_version found${NC}"
        return 0
    else
        echo -e "${RED}   ❌ Node.js not found${NC}"
        return 1
    fi
}

echo -e "${YELLOW}🔍 Checking system requirements...${NC}"

# Check for required system dependencies
MISSING_DEPS=false

echo -e "${BLUE}   Checking Python...${NC}"
check_python_version
python_check_result=$?
if [ "$python_check_result" -eq 1 ]; then
    echo -e "${RED}   Please install Python 3.8+ from https://python.org${NC}"
    MISSING_DEPS=true
elif [ "$python_check_result" -eq 2 ]; then
    echo -e "${YELLOW}   📋 Python 3.13+ compatibility note:${NC}"
    echo -e "${YELLOW}   If you encounter install errors, consider using Python 3.11 or 3.12${NC}"
    echo -e "${YELLOW}   You can install via: brew install python@3.11 (macOS) or pyenv${NC}"
fi

echo -e "${BLUE}   Checking Node.js...${NC}"
if ! check_node_version; then
    echo -e "${RED}   Please install Node.js 16+ from https://nodejs.org${NC}"
    MISSING_DEPS=true
fi

echo -e "${BLUE}   Checking npm...${NC}"
if command_exists npm; then
    npm_version=$(npm --version)
    echo -e "${GREEN}   ✅ npm $npm_version found${NC}"
else
    echo -e "${RED}   ❌ npm not found (should come with Node.js)${NC}"
    MISSING_DEPS=true
fi

echo -e "${BLUE}   Checking FFmpeg (for video processing)...${NC}"
if command_exists ffmpeg; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n1 | cut -d' ' -f3)
    echo -e "${GREEN}   ✅ FFmpeg $ffmpeg_version found${NC}"
elif command_exists brew; then
    echo -e "${YELLOW}   ⚠️  FFmpeg not found but Homebrew is available${NC}"
    echo -e "${BLUE}   Installing FFmpeg via Homebrew...${NC}"
    if brew install ffmpeg; then
        echo -e "${GREEN}   ✅ FFmpeg installed successfully${NC}"
    else
        echo -e "${YELLOW}   ⚠️  FFmpeg installation failed, will use demo mode${NC}"
    fi
else
    echo -e "${YELLOW}   ⚠️  FFmpeg not found (video processing will use demo mode)${NC}"
    echo -e "${YELLOW}   Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)${NC}"
fi

if [ "$MISSING_DEPS" = true ]; then
    echo ""
    echo -e "${RED}❌ Missing required dependencies. Please install them and run setup again.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All system requirements met!${NC}"
echo ""

# Clean up any junk files from previous runs
if find . -name "=*" -type f -print -quit | grep -q "=" 2>/dev/null; then
    echo -e "${YELLOW}🧹 Cleaning up junk files...${NC}"
    find . -name "=*" -type f -delete
    echo -e "${GREEN}   ✅ Cleaned up junk files${NC}"
fi

# Setup Backend
echo -e "${YELLOW}🐍 Setting up Backend (Python)...${NC}"

if [ ! -d "backend" ]; then
    echo -e "${RED}❌ Backend directory not found!${NC}"
    echo "Make sure you're running this from the project root directory."
    exit 1
fi

cd backend

# Create virtual environment
echo -e "${BLUE}   Creating Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}   Virtual environment already exists, removing old one...${NC}"
    rm -rf venv
fi

# Choose Python version based on flag or availability
if [ "$USE_PYTHON311" = true ]; then
    if command_exists python3.11; then
        echo -e "${GREEN}   Using Python 3.11${NC}"
        python3.11 -m venv venv
    else
        echo -e "${RED}   ❌ Python 3.11 not found! Install with: brew install python@3.11${NC}"
        exit 1
    fi
else
    python3 -m venv venv
fi
echo -e "${GREEN}   ✅ Virtual environment created${NC}"

# Activate virtual environment and install dependencies
echo -e "${BLUE}   Installing Python dependencies...${NC}"
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install the package in development mode
if [ -f "pyproject.toml" ]; then
    echo -e "${BLUE}   Installing backend package and dependencies...${NC}"
    if pip install -e .; then
        echo -e "${GREEN}   ✅ Backend dependencies installed${NC}"
    else
        echo -e "${RED}   ❌ Failed to install backend dependencies${NC}"
        echo ""
        echo -e "${YELLOW}🔧 Troubleshooting Python 3.13 compatibility issues:${NC}"
        echo ""
        echo -e "${BLUE}Option 1: Use a compatible Python version${NC}"
        echo -e "   1. Install Python 3.11: ${GREEN}brew install python@3.11${NC}"
        echo -e "   2. Create venv with 3.11: ${GREEN}python3.11 -m venv venv${NC}"
        echo -e "   3. Re-run setup: ${GREEN}./setup.sh${NC}"
        echo ""
        echo -e "${BLUE}Option 2: Try installing problematic packages individually${NC}"
        echo -e "   1. Activate venv: ${GREEN}source venv/bin/activate${NC}"
        echo -e "   2. Install torch first: ${GREEN}pip install torch${NC}"
        echo -e "   3. Install whisper: ${GREEN}pip install git+https://github.com/openai/whisper.git${NC}"
        echo -e "   4. Install remaining: ${GREEN}pip install -e .${NC}"
        echo ""
                 echo -e "${BLUE}Option 3: Use pyenv for version management${NC}"
         echo -e "   1. Install pyenv: ${GREEN}brew install pyenv${NC}"
         echo -e "   2. Install Python 3.11: ${GREEN}pyenv install 3.11.7${NC}"
         echo -e "   3. Set local version: ${GREEN}pyenv local 3.11.7${NC}"
         echo -e "   4. Re-run setup: ${GREEN}./setup.sh${NC}"
         echo ""
         echo -e "${BLUE}Option 4: Fix FFmpeg/Santa issues (Shopify environments)${NC}"
         echo -e "   1. Run: ${GREEN}./fix-ffmpeg.sh${NC}"
         echo -e "   2. Then: ${GREEN}./remove-bundled-ffmpeg.sh${NC}"
         echo ""
         exit 1
    fi
else
    echo -e "${RED}   ❌ pyproject.toml not found${NC}"
    exit 1
fi

cd ..

# Setup Frontend
echo -e "${YELLOW}⚛️  Setting up Frontend (Node.js)...${NC}"

if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Frontend directory not found!${NC}"
    echo "Make sure you're running this from the project root directory."
    exit 1
fi

cd frontend

# Install Node.js dependencies
echo -e "${BLUE}   Installing Node.js dependencies...${NC}"
if [ -f "package.json" ]; then
    # Clean install
    if [ -d "node_modules" ]; then
        echo -e "${YELLOW}   Removing existing node_modules...${NC}"
        rm -rf node_modules
    fi
    
    if [ -f "package-lock.json" ]; then
        npm ci
    else
        npm install
    fi
    echo -e "${GREEN}   ✅ Frontend dependencies installed${NC}"
else
    echo -e "${RED}   ❌ package.json not found${NC}"
    exit 1
fi

cd ..

# Create output directories if they don't exist
echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
mkdir -p backend/app/output_clips
echo -e "${GREEN}   ✅ Output directories created${NC}"

# Make scripts executable
echo -e "${YELLOW}🔐 Setting script permissions...${NC}"
chmod +x start.sh
if [ -f "frontend/run-dev.sh" ]; then
    chmod +x frontend/run-dev.sh
fi
echo -e "${GREEN}   ✅ Script permissions set${NC}"

echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "======================================"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "${BLUE}1.${NC} Run the application: ${GREEN}./start.sh${NC}"
echo -e "${BLUE}2.${NC} Open your browser:"
echo -e "   • Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "   • Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "   • API Documentation: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}📁 Project structure:${NC}"
echo -e "   • ${BLUE}backend/${NC} - Python FastAPI server"
echo -e "   • ${BLUE}frontend/${NC} - Next.js React application"
echo -e "   • ${BLUE}start.sh${NC} - Starts both frontend and backend"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo -e "   • Use ${GREEN}./start.sh${NC} to run both services"
echo -e "   • Press ${GREEN}Ctrl+C${NC} to stop all services"
echo -e "   • Logs are saved to backend.log and frontend.log"
echo ""
echo -e "${YELLOW}🔧 Having compatibility issues?${NC}"
echo -e "   • Python 3.13+: ${GREEN}./setup.sh --python311${NC} or ${GREEN}brew install python@3.11${NC}"
echo -e "   • FFmpeg/Santa: ${GREEN}./fix-ffmpeg.sh${NC} (for Shopify environments)"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}" 