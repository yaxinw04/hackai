FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    USE_SYSTEM_FFMPEG=1 \
    FFMPEG_BINARY=/usr/bin/ffmpeg

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install Python dependencies directly (more reliable for production)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        fastapi>=0.104.0 \
        uvicorn[standard]>=0.24.0 \
        python-multipart>=0.0.6 \
        pydantic>=2.0.0 \
        numpy>=1.21.0 \
        requests>=2.28.0 \
        yt-dlp>=2023.7.6 \
        moviepy>=1.0.3 \
        pydub>=0.25.1 \
        transformers>=4.30.0 \
        openai>=1.0.0 \
        boto3>=1.28.0 \
        gunicorn>=21.0.0 \
        python-dotenv>=1.0.0 \
        setuptools \
        wheel \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy application code
COPY app/ ./app/

# Create necessary directories and set permissions
RUN mkdir -p /app/output_clips /app/temp \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout", "300", "app.main:app"] 