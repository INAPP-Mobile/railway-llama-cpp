# LLaMA.cpp Inference Server — Railway Template

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/new/template/lR5GrQ)

A lightweight, OpenAI-compatible LLM inference server powered by [llama-cpp-python](https://github.com/abetlen/llama-cpp-python). Drop GGUF-format models into a persistent volume and instantly serve requests via standard OpenAI API endpoints — no GPU required.

## Features

- **Minimal resource usage** — ~50–200 MB baseline RAM, runs comfortably on Railway's Hobby tier
- **OpenAI-compatible API** — Drop-in replacement for `/v1/completions`, `/v1/chat/completions`, and `/v1/models`
- **GGUF model support** — Load any GGUF-quantized model: Llama, Mistral, Phi, Qwen, DeepSeek, and hundreds more from Hugging Face
- **CPU-optimized** — Multi-threaded inference out of the box; optional CUDA/OpenCL/Vulkan support for Pro tier
- **Small image** — ~300 MB (Python + compiled binary) vs 500 MB+ for full LM Studio images
- **On-demand model loading** — Models load on first request, not at build time
- **Persistent model storage** — Railway volume keeps your models across redeploys
- **Hugging Face Hub integration** — Auto-download models directly from Hugging Face with `huggingface_hub` pre-installed

## Deploy

Click the button above or follow these steps:

1. **Deploy** the template to your Railway account (creates the service + volume)
2. **Add GGUF models** via the Railway dashboard file manager, or use `huggingface_hub` to pull them directly
3. **Use the API** immediately — your service URL is ready as soon as the build completes

### Getting Models

**Option A — Hugging Face Hub (easiest):**
Set `MODEL_REPO_ID` in the deploy form to a GGUF-containing repo (e.g., `unsloth/Meta-Llama-3.1-8B-Instruct-GGUF`). The server auto-downloads models on first request.

**Option B — Upload manually:**
Upload `.gguf` files to the mounted volume at `/opt/models/.cache/huggingface` using the Railway dashboard file manager or via CLI.

**Option C — Existing volume:**
If you already have a Railway volume with GGUF models, mount it at the same path.

**Recommended starter models:**
| Model | Size | Notes |
|-------|------|-------|
| `Llama-3.2-3B-Instruct-Q4_K_M.gguf` | ~2 GB | Fast, capable for most tasks |
| `Mistral-7B-Instruct-v0.3-Q4_K_M.gguf` | ~4 GB | Good balance of speed/quality |
| `Phi-3-mini-4k-instruct-Q4_K_M.gguf` | ~2 GB | Microsoft's efficient small model |
| `Qwen2.5-7B-Instruct-Q4_K_M.gguf` | ~4.5 GB | Strong instruction following |

### Quick Test with the CLI

A companion test script (`chat.py`, copied to `/app/chat.py` in the container) is included in this template for quick smoke tests.

**Which URL to use:**

| Where `chat.py` runs | `--url` value | External URL needed? |
|---------------------|-------------|----------------------|
| Same container (Railway `service exec`) | `http://localhost:8000` (default) | No |
| Local dev (server on your laptop) | `http://localhost:8000` (default) | No |
| Another Railway service (same network) | `http://railway-llama-cpp.railway.internal:8000` | No (private DNS) |
| Your laptop → deployed instance | `https://<your-service>.up.railway.app` | Yes |

```bash
# No --url needed when running on the same machine/container (defaults to localhost:8000):
python chat.py
python chat.py --list-models
python chat.py --health

# From your laptop against the deployed instance (needs public URL):
python chat.py --url https://railway-llama-cpp-production.up.railway.app

# List mounted models:
python chat.py --list-models --url https://railway-llama-cpp-production.up.railway.app

# Stream a custom prompt:
python chat.py --url https://railway-llama-cpp-production.up.railway.app \
  --prompt "Write a haiku about llamas" --stream

# Test the /v1/completions endpoint:
python chat.py --url https://railway-llama-cpp-production.up.railway.app \
  --prompt "Once upon a time" --completion --max-tokens 100

# Check server health:
python chat.py --url https://railway-llama-cpp-production.up.railway.app --health
```

### Verify It's Working

```bash
# Health check
curl https://<your-service-url>/health

# Text completion
curl https://<your-service-url>/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"default","prompt":"Hello! What can you do?","max_tokens":100}'

# Chat completion
curl https://<your-service-url>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"default","messages":[{"role":"user","content":"Tell me a short joke"}],"max_tokens":100}'
```

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `MODEL_PATH` | `/opt/models/.cache/huggingface` | Yes | Directory where GGUF files are loaded from (Railway volume mount point) |
| `N_THREADS` | `4` | No | CPU threads for inference. Increase for multi-core CPUs |
| `N_CTX` | `4096` | No | Context window size in tokens. Increase for longer conversations (e.g., `8192`, `16384`) |
| `DEFAULT_MODEL` | _(empty)_ | No | Specific `.gguf` filename to load instead of auto-detecting the first file |
| `MODEL_REPO_ID` | _(empty)_ | No | Hugging Face repo ID for auto-downloading GGUF models on startup. Example: `unsloth/Meta-Llama-3.1-8B-Instruct-GGUF` |
| `HF_TOKEN` | _(empty)_ | No | Hugging Face access token for downloading from **private** repos. Use Railway's secret store for this value |

## Pairing with Open WebUI

This server works as a drop-in OpenAI endpoint for any OpenAI-compatible frontend:

1. Deploy [Open WebUI](https://railway.com/new/template/open-webui) on Railway
2. In Open WebUI admin settings, add a new OpenAI connection:
   - **URL:** `http://llama-cpp.railway.internal:8000/v1`
   - **API Key:** leave blank (or any placeholder)
3. Your GGUF models appear in the model picker automatically

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Returns HTTP 200 when the server is ready |
| `/v1/models` | GET | Lists available models from mounted GGUF files |
| `/v1/completions` | POST | OpenAI-compatible text completions |
| `/v1/chat/completions` | POST | OpenAI-compatible chat completions |

## Architecture

```
┌─────────────────┐
│   Railway CDN   │ ◄── Public traffic
└────────┬────────┘
         │
┌────────▼────────┐
│  LLaMA.cpp      │ ◄── FastAPI + llama-cpp-python
│  Container      │     - Port 8000
│                 │     - /health endpoint
├─────────────────┤
│  models volume  │ ◄── Persistent GGUF storage
│  (persistent)   │     - Mounted at /opt/models/.cache/huggingface
└─────────────────┘
```

## Why This Instead of Ollama?

| | LLaMA.cpp (this template) | Ollama |
|--|--------------------------|--------|
| **Image size** | ~300 MB | ~2–5 GB (model images) |
| **RAM baseline** | ~50 MB | ~200 MB+ |
| **GPU required** | No (CPU-optimized) | Yes (GPU strongly recommended) |
| **Model format** | GGUF (download once) | GGUF + Ollama manifest (modelfile) |
| **API** | OpenAI-compatible natively | Requires proxy layer |
| **Startup time** | ~10–30 seconds | ~2–5 minutes (model pull) |

## Resources

- [llama-cpp-python Documentation](https://github.com/abetlen/llama-cpp-python)
- [GGUF Model Format](https://github.com/ggml-org/gguf)
- [Hugging Face GGUF Models](https://huggingface.co/models?library=gguf)
- [Railway Docs](https://docs.railway.com)