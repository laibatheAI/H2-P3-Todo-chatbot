# Production Dockerfile for FastAPI Todo AI Chatbot
# Hugging Face Spaces Docker Deployment
# Configured for Neon PostgreSQL (cloud database)

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

# Set working directory
WORKDIR /app

# Install system dependencies for PostgreSQL driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Expose Hugging Face Spaces required port
EXPOSE 7860

# Run the application (note: main.py is in src/)
# Application will connect to Neon PostgreSQL via DATABASE_URL environment variable
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860" , "--reload"]
