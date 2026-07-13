#!/bin/sh
# Docker entrypoint for llama.cpp inference server
# Handles volume permissions and starts the uvicorn server

set -e

# Handle volume mount permissions (Railway volumes are owned by root)
MODEL_PATH="${MODEL_PATH:-/opt/models/.cache/huggingface}"
mkdir -p "$MODEL_PATH"
if [ ! -d "$MODEL_PATH" ]; then
    echo "Creating model directory: $MODEL_PATH"
    mkdir -p "$MODEL_PATH"
fi

# Download models from Hugging Face if requested and none exist yet
gguf_count=$(find "$MODEL_PATH" -maxdepth 1 -name "*.gguf" | wc -l)
if [ -z "$MODEL_REPO_ID" ]; then
    echo "No MODEL_REPO_ID set, skipping auto-download."
elif [ $gguf_count -eq 0 ]; then
    echo "No models found. Downloading from Hugging Face repo: $MODEL_REPO_ID..."
    python -c "from huggingface_hub import snapshot_download; \
            snapshot_download(repo_id='$MODEL_REPO_ID', allow_patterns='*.gguf', local_dir='$MODEL_PATH')" || {
        echo "Warning: Failed to download models. Continuing without them."
    }
else
    echo "Found existing GGUF files in $MODEL_PATH, skipping auto-download."
fi

export MODEL_PATH
chmod -R 777 "$MODEL_PATH" 2>/dev/null || true

# Export the port for uvicorn
PORT="${PORT:-8000}"
export PORT

# Exit if still need user auth? Not needed: user sets token via env var later.

# Execute the main command
exec "$@"
