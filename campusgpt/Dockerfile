# Use official lightweight Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

WORKDIR /app

# Install system dependencies for PDF parsing and C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Sentence Transformer models to bake them into the Docker image
# RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Copy application files
COPY . .

# Create database and data folders and make them writeable for non-root Hugging Face user (UID 1000)
RUN mkdir -p /app/chroma_db /app/data /app/extracted && chmod -R 777 /app

# Expose port
EXPOSE 7860

# Start Uvicorn ASGI server
CMD uvicorn app:app --host 0.0.0.0 --port $PORT

