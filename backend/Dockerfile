# MotionIQ FastAPI Backend Dockerfile
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies required for OpenCV, MediaPipe, FFmpeg, and healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libegl1 \
    libgles2 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and migrations
COPY . .

# Ensure storage directories and model directories exist
RUN mkdir -p /app/storage/raw_videos \
             /app/storage/temp_videos \
             /app/storage/annotated_videos \
             /app/storage/reports \
             /app/storage/analyses \
             /app/app/models

# If MediaPipe model doesn't exist locally, download it
RUN if [ ! -f /app/app/models/pose_landmarker_lite.task ]; then \
        python download_model.py; \
    fi

# Set permissions for startup script
RUN chmod +x /app/start.sh

# Expose backend port
EXPOSE 10000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

# Start server using the migration and startup script
CMD ["/app/start.sh"]
