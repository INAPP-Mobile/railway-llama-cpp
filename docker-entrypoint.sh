#!/bin/sh
# Docker entrypoint for llama.cpp inference server
# Handles volume permissions and starts the uvicorn server

set -e

# Handle volume mount permissions (Railway volumes are owned by root)
MODEL_PATH="${MODEL_PATH:-/opt/models/.cache/huggingface}"
if [ -d "$MODEL_PATH" ]; then
    # Ensure we can read/write the model directory
    chmod -R 777 "$MODEL_PATH" 2>/dev/null || true
fi

# Export the port for uvicorn
PORT="${PORT:-8000}"
export PORT

# Execute the main command
exec "$@"