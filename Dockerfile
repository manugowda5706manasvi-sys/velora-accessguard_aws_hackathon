# Production Container for AccessGuard AI
FROM python:3.12-slim

# Prevent Python from writing .pyc and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and dataset
COPY backend/ ./backend/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Ensure data directory exists
RUN mkdir -p data

EXPOSE 8000

# Run uvicorn on container port
CMD exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}
