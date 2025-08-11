# Production Dockerfile for Puch.AI MCP Chatbot Server
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash puch
RUN chown -R puch:puch /app
USER puch

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command - run persistent server
CMD ["python", "main.py", "--server-persistent"]

# Expose port for potential HTTP interface (future)
EXPOSE 8000

# Labels
LABEL maintainer="Puch.AI Team"
LABEL description="Production MCP Chatbot Server with AI Chat, Weather, and Search"
LABEL version="1.0.0"