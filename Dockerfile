# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install build dependencies for llama-cpp-python (optional CUDA support via env)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git cmake build-essential libcurl4-openssl-dev libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# Install llama-cpp-python with OpenBLAS backend for CPU optimization
# CUDA support: set LLAMA_CUDA=1 environment variable before pip install
RUN pip install --no-cache-dir llama-cpp-python fastapi uvicorn huggingface_hub

# Create model storage directory
RUN mkdir -p /opt/models/.cache/huggingface

# Set working directory
WORKDIR /app

# Copy the FastAPI application
COPY --chmod=755 app.py /app/app.py
COPY --chmod=755 chat.py /app/chat.py
COPY --chmod=755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Switch to root for volume permission handling
USER root

# Runtime volume mount for models

# Expose port
EXPOSE 8000

# Set environment defaults (these are inherited by all processes in the container)
ENV PORT=8000
ENV MODEL_PATH=/opt/models/.cache/huggingface

# Hugging Face CLI cache paths - ensure models persist in volume
ENV HUGGING_FACE_HUB_CACHE=/opt/models/.cache/huggingface
ENV TRANSFORMERS_CACHE=/opt/models/.cache/huggingface/transformers

# Start server - PORT env var injected by Railway, default 8000
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD [ "uvicorn", "app:fastapi_app", "--host", "0.0.0.0", "--port", "8000" ]
