#!/bin/sh
# Docker entrypoint for llama.cpp inference server
# Handles volume permissions and starts the uvicorn server

set -e

# Handle volume mount permissions (Railway volumes are owned by root)
MODEL_PATH="${MODEL_PATH:-/opt/models/.cache/huggingface}"
mkdir -p "$MODEL_PATH"

# Export MODEL_PATH after ensuring directory exists
export MODEL_PATH
export HUGGING_FACE_HUB_CACHE=/opt/models/.cache/huggingface
export TRANSFORMERS_CACHE=/opt/models/.cache/huggingface/transformers

# Make volume writable for the app if needed
if [ ! -w "$MODEL_PATH" ]; then
  echo "Model path not writable, attempting to fix permissions..."
  chmod -R 755 "$MODEL_PATH" || true
fi

# Export the port for uvicorn
PORT="${PORT:-8000}"
export PORT

# Execute the main command
exec "$@"