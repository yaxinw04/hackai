# YouTube to Shorts Service

A full-stack web application that converts YouTube videos into engaging short clips using AI-powered video processing.

## ⚡ Quick Start

**First time setup? Choose your setup method:**

### 🚀 For Restricted/Corporate Environments (Recommended)
```bash
# Minimal setup that works in most environments:
./setup-minimal.sh
```

### 🔧 For Full Development Environment
```bash
# Complete setup with all video processing features:
./setup.sh
```

**Then start all services:**

```bash
# From the project root directory:
./start.sh
```

That's it! 🎉 The setup script handles dependencies, and start script launches everything.

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

Press `Ctrl+C` to stop all services.

---

## 🎯 Overview

This service consists of three main components:

- **Backend**: FastAPI server that handles video processing requests and serves generated clips
- **Frontend**: Next.js web interface for submitting videos and viewing results  
- **Video Processor**: Python modules for video processing (already exists in `ml_stuff/processors/`)

## 🏗️ Architecture

```
┌─────────────────┐    API calls    ┌─────────────────┐    Calls    ┌─────────────────┐
│                 │ ──────────────→ │                 │ ──────────→ │                 │
│  Next.js        │                 │  FastAPI        │             │  ml_stuff/      │
│  Frontend       │ ←────────────── │  Backend        │ ←────────── │  processors/    │
│  (port 3000)    │   Video clips   │  (port 8000)    │  Results    │                 │
└─────────────────┘                 └─────────────────┘             └─────────────────┘
```

## 📋 Prerequisites

Before setting up the frontend and backend, ensure you have:

1. **Python 3.8+** with pip
2. **Node.js 18+** with npm
3. **Video Processing Modules**: The `ml_stuff/processors/` directory contains your existing video processing code

### Video Processing Modules

Your existing video processing code in `ml_stuff/processors/` includes:
- `transcribe.py` - Video transcription using Whisper
- `segments.py` - Segment detection and scoring using transformers
- `captions.py` - Caption generation using OpenAI API

The backend integrates these modules with additional functionality:
- `ml_stuff/pipeline.py` - Complete pipeline wrapper that downloads YouTube videos, processes them, and creates video clips

### Required Dependencies

The system requires several Python packages for video processing:
- **yt-dlp** - For downloading YouTube videos
- **moviepy** - For creating video clips
- **whisper** - For audio transcription
- **transformers** - For sentiment analysis
- **pydub** - For audio processing
- **openai** - For caption generation (requires API key)

### Environment Variables

For full functionality, set these environment variables:
- `OPENAI_API_KEY` - Required for caption generation (optional, will work without captions)

## 🚀 Setup Instructions

### 🎯 Choose Your Setup Method

#### **Option 1: Minimal Setup (Recommended for Most Users)**

Perfect for restricted environments, corporate networks, or quick testing:

```bash
# Minimal setup that works everywhere:
./setup-minimal.sh
```

This will install:
- ✅ FastAPI web server and core dependencies
- ✅ Frontend React/Next.js components  
- ✅ Basic API functionality with mock data
- ✅ Core video processing pipeline (limited functionality)

#### **Option 2: Complete Setup (Full Features)**

For full development with all video processing capabilities:

```bash
# Complete setup with all features:
./setup.sh
```

This will additionally install:
- ✅ PyTorch and AI/ML libraries
- ✅ Video processing tools (requires ffmpeg)
- ✅ Real transcription and video editing
- ✅ Full OpenAI integration

**Then start the services:**
```bash
./start.sh
```

### 🔧 Manual Setup (If Needed)

If you prefer to set up manually or need to troubleshoot:

#### 1. Backend Setup

```bash
# Use make command for easy setup
make setup-backend

# OR manually:
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

#### 2. Frontend Setup

```bash
# Use make command for easy setup
make setup-frontend

# OR manually:
cd frontend
npm install
```

## 🏃‍♂️ Running the Application

**🎯 EASY WAY - Single Command from Root Directory:**

You can now start both services with a single command from the project root:

### Option 1: Shell Script (Recommended)
```bash
./start.sh
```

### Option 2: NPM Script
```bash
npm start
# or
npm run dev
```

### Option 3: Make Command
```bash
make start
# or just
make
```

### Option 4: Node.js Script (with concurrently)
```bash
./dev.js
```

All of these commands will:
- ✅ Automatically check and install dependencies
- ✅ Start both backend and frontend servers
- ✅ Show colored output with service logs
- ✅ Handle graceful shutdown with Ctrl+C
- ✅ Display service URLs when ready

**📍 Service URLs:**
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

**🔧 MANUAL WAY - Separate Terminals (if needed):**

### Terminal 1: Start the Backend Server

```bash
cd backend
source venv/bin/activate  # If using virtual environment
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Start the Frontend Server

```bash
cd frontend
npm run dev
```

## 🎮 Usage

1. **Open your browser** and navigate to `http://localhost:3000`

2. **Enter a YouTube URL** in the first input field
   - Example: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`

3. **Describe your clip requirements** in the prompt field
   - Example: "Create 3 engaging clips highlighting the main topics"
   - Example: "Extract funny moments and create 30-second clips"

4. **Click "Create Clips"** to start processing

5. **Monitor progress** - The interface will show real-time status updates

6. **View and download results** - Once complete, you can preview and download the generated clips

## 📁 Project Structure

```
├── README.md
├── setup-minimal.sh            # 🚀 Minimal setup script (recommended)
├── setup.sh                    # 🔧 Complete setup script (full features)
├── start.sh                    # 🚀 Main startup script (daily use)
├── dev.js                      # 🔧 Node.js development server
├── package.json               # 📦 Root package.json with scripts
├── Makefile                   # 🛠️ Make commands for development
├── backend/                    # FastAPI Backend
│   ├── pyproject.toml         # Python dependencies
│   ├── .gitignore
│   └── app/
│       ├── __init__.py
│       ├── main.py            # FastAPI app with endpoints
│       ├── schemas.py         # Pydantic models
│       └── output_clips/      # Generated video clips
│           └── .gitkeep
├── frontend/                   # Next.js Frontend
│   ├── package.json           # Node.js dependencies
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── .gitignore
│   └── src/
│       ├── app/
│       │   ├── layout.tsx     # Root layout
│       │   ├── page.tsx       # Main page with form
│       │   └── globals.css    # Global styles
│       └── services/
│           └── apiClient.ts   # API communication
└── ml_stuff/                   # Video Processing (Your existing code)
    ├── processors/
    │   ├── transcribe.py      # Video transcription
    │   ├── segments.py        # Segment detection & scoring  
    │   └── captions.py        # Caption generation
    ├── test.py                # Test script for processors
    └── zipline.mov            # Sample video file
```

## 🎛️ Available Commands

### Setup Commands (Run Once)
```bash
./setup-minimal.sh  # Minimal setup for restricted environments (RECOMMENDED)
./setup.sh          # Complete setup with all video processing features
make setup-minimal  # Same as minimal setup
make setup          # Same as complete setup
npm run setup:minimal # Minimal setup via npm
npm run setup       # Complete setup via npm
make setup-quick    # Quick manual setup
```

### Start Commands (Daily Use)
```bash
./start.sh          # Start all services (recommended)
npm start           # Same as above, using npm
npm run dev         # Same as above, development mode
make start          # Using Make
make dev            # Same as above
./dev.js            # Node.js version with concurrently
```

### Development Commands
```bash
make setup-backend  # Setup only backend
make setup-frontend # Setup only frontend
make backend        # Run only backend server
make frontend       # Run only frontend server
make clean          # Clean all build artifacts
make logs           # View logs from running services
make help           # Show all available commands
```

### NPM Scripts (from root directory)
```bash
npm run setup:quick # Quick setup both services
npm run backend     # Run only backend
npm run frontend    # Run only frontend
npm run clean       # Clean project
npm run logs        # View logs
```

## 🔧 API Endpoints

### Backend API (`http://localhost:8000`)

- `GET /` - Health check and API info
- `POST /process` - Start video processing
  ```json
  {
    "url": "https://youtube.com/watch?v=...",
    "prompt": "Create engaging clips..."
  }
  ```
- `GET /status/{job_id}` - Get processing status
- `GET /clips/{filename}` - Serve generated video files
- `GET /jobs` - List all jobs (debug endpoint)

## ⚠️ Troubleshooting

### Setup Issues

**General setup problems or restricted environment**
```bash
# Try the minimal setup instead:
./setup-minimal.sh
# This works in most environments with fewer dependencies
```

**Python 3.13 compatibility issues**
```bash
# Use minimal setup which avoids problematic packages:
./setup-minimal.sh
```

### Backend Issues

**Error: "Video processor is not available"**
```bash
# Ensure your ml_stuff directory contains the processors
ls ml_stuff/processors/
# Should show: transcribe.py, segments.py, captions.py

# Check if the backend can import your modules
cd backend && source venv/bin/activate
python -c "import sys; sys.path.append('../'); from ml_stuff.processors import transcribe, segments, captions; print('✅ Processors imported successfully')"
```

**Error: "ModuleNotFoundError: No module named 'ml_stuff'"**
```bash
# Make sure you're running from the project root directory
pwd  # Should show path ending with your project name
ls   # Should show both ml_stuff/ and backend/ directories
```

**Port 8000 already in use**
```bash
# Use a different port
uvicorn app.main:app --reload --port 8001
# Update frontend/src/services/apiClient.ts accordingly
```

### Frontend Issues

**Error: "Network error occurred"**
- Ensure the backend server is running on `http://localhost:8000`
- Check browser console for CORS errors
- Verify the API base URL in `frontend/src/services/apiClient.ts`

**Port 3000 already in use**
```bash
# Next.js will automatically prompt to use port 3001
# Or specify a different port:
npm run dev -- --port 3001
```

**Build errors**
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

### General Issues

**Processing takes too long**
- Large YouTube videos can take several minutes to process
- Video download, transcription, and clip creation are CPU-intensive
- Check backend logs for progress updates
- Ensure sufficient disk space in `backend/app/output_clips/`

**Generated clips not loading**
- Check if files exist in `backend/app/output_clips/`
- Verify static file serving is working: `http://localhost:8000/clips/`
- Check browser console for 404 errors

**"yt-dlp not installed" error**
```bash
cd backend && source venv/bin/activate
pip install yt-dlp
```

**"moviepy not installed" error**
```bash
cd backend && source venv/bin/activate
pip install moviepy
```

**Whisper/Transcription errors**
```bash
# Install torch first (required for Whisper)
cd backend && source venv/bin/activate
pip install torch
pip install openai-whisper
```

**OpenAI API errors (caption generation)**
```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
# Or create a .env file in the backend directory
echo "OPENAI_API_KEY=your-api-key-here" > backend/.env
```

**"No clips generated" but processing completes**
- Check if moviepy is installed and working
- Video clips might fail to create but processing info is still saved
- Check `backend/app/output_clips/` for `.txt` files with clip information

**Strange files with names like `=0.104.0`, `=2.0.0` appear**
- These are junk files created by typing `>` instead of `==` in pip commands
- They are automatically cleaned up by `./setup.sh` and `./start.sh`
- You can manually delete them with: `find . -name "=*" -type f -delete`
- They are ignored by Git (won't be committed)

## 🔒 Environment Variables

### Backend
Create `backend/.env` for custom configuration:
```env
# Custom output directory (optional)
OUTPUT_DIR="/path/to/custom/output"

# API settings
HOST=0.0.0.0
PORT=8000
```

### Frontend
Create `frontend/.env.local` for custom API endpoint:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🧪 Development

### Backend Development
```bash
cd backend
# Run with auto-reload
uvicorn app.main:app --reload

# Run tests (if implemented)
pytest

# Format code
black app/
```

### Frontend Development
```bash
cd frontend
# Development server with hot reload
npm run dev

# Type checking
npm run lint

# Build for production
npm run build
```

## 📈 Production Deployment

### Backend
```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend
```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Need help?** Check the troubleshooting section above or open an issue on GitHub.
