#!/bin/bash

# Production startup script for backend
# This runs in containerized environments (DigitalOcean App Platform, Docker, etc.)

set -e

echo "🚀 Starting YouTube Shorts Backend (Production)"
echo "=============================================="

# Install dependencies if needed (for buildpack deployments)
if [ ! -d "venv" ] && [ -f "pyproject.toml" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -e .
fi

# Set environment variables for FFmpeg
export USE_SYSTEM_FFMPEG=1
export FFMPEG_BINARY=$(which ffmpeg 2>/dev/null || echo "/usr/bin/ffmpeg")

echo "🎬 FFmpeg path: $FFMPEG_BINARY"

# Start the FastAPI application
echo "🚀 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 