# LLaMA.cpp Inference Server — Railway Template

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/new/template/llama-cpp)

A standalone OpenAI-compatible inference server powered by llama-cpp-python, optimized for Railway's Hobby tier with minimal resource footprint. Drop GGUF-format models into a mounted volume and immediately serve LLM requests via standard API endpoints.

## Features

- **Minimal resource usage** — ~50-200MB baseline RAM (vs 150MB+ for LM Studio CLI)
- **OpenAI-compatible API** — Drop-in replacement for OpenAI endpoints `/v1/completions` and `/v1/chat/completions`
- **GGUF model support** — Load any GGUF-quantized model (Llama, Mistral, Phi, etc.)
- **CPU-optimized** — Single-threaded and multi-threaded inference with optional CUDA/OpenCL/Vulkan support for Pro tier
- **Small image size** — ~300MB (Python + compiled lib) vs 500MB+ for full LM Studio images
- **On-demand model loading** — Models load on first request, not pre-downloaded at build time

## Architecture

```
┌─────────────────┐
│   Railway CDN   │ ◄── Production traffic
└────────┬────────┘
         │
┌────────▼────────┐
│  LLaMA.cpp      │ ◄── FastAPI + llama-cpp-python (Docker)
│  Container      │     - /health endpoint
│                 │     - PORT=8000
├─────────────────┤
│  models volume  │ ◄── Persistent GGUF model storage
└─────────────────┘
```

## Deploy and Host

### About Hosting

The LLaMA.cpp server runs as a single Docker container with a persistent volume for model storage. It uses llama-cpp-python with optional CUDA acceleration.

- **Default Port:** 8000 (Railway auto-injects `PORT`)
- **Health Check:** `GET /health` — returns HTTP 200 when ready
- **Startup Time:** ~10-30 seconds (model loads on first request)
- **Resource Usage:** ~200MB RAM baseline (model-dependent)

### Connecting Models

After deploying, you need to add GGUF model files to the mounted volume:

1. Download a GGUF model (e.g., from Hugging Face Hub)
2. Upload the `.gguf` file to `/opt/models/.cache/huggingface` in the Railway volume
3. Or mount an existing volume containing GGUF models

**Example models:**
- `llama-2-7b.Q4_0.gguf` — Small, fast inference
- `mistral-7b-v0.1.Q4_0.gguf` — Good balance of speed/quality
- `phi-3-mini-4k-instruct.Q4_0.gguf` — Microsoft Phi-3

## Environment Variables

| Variable      | Default                                | Description |
|--------------|----------------------------------------|-------------|
| `MODEL_PATH` | `/opt/models/.cache/huggingface`       | Directory where GGUF files are loaded from (Railway volume mount) |
| `DEFAULT_MODEL` | _(empty)_                          | Optional specific model filename to load by default |
| `N_THREADS`   | `4` | CPU threads for inference (adjust for your CPU) |
| `N_CTX`       | `4096` | Context window size in tokens (higher = more memory) |
| `MODEL_REPO_ID` | _(empty)_ | Hugging Face repo with GGUF models to auto-download on startup (requires HF token if private repo; use secret store env var). Example: `unsloth/Meta-Llama-3.1-8B-Instruct-GGUF` |

## Getting Started

1. Click the **Deploy on Railway** button above
2. Wait for the build to complete (usually < 2 minutes)
3. Add GGUF models to the mounted volume:
   - Use the Railway dashboard file manager, or
   - Via SSH: `./scripts/railway.sh service ssh --service railway-llama-cpp` then copy with `scp your-model.gguf /opt/models/.cache/huggingface/`
4. Test the endpoint: `curl http://<railway-domain>/v1/completions -d '{"model":"default","prompt":"Hello","max_tokens":50}'`
5. Hit `/health` — returns HTTP 200 once the app is running

### Manually downloading models with huggingface_hub (optional)

If you prefer not to browse file managers, you can manually download GGUF models using the pre-installed Hugging Face Hub library:

```bash
# Via Railway service exec (one-liner):
./scripts/railway.sh service exec --project f6ac9cac-7456-4977-98db-0f5d57e56eba -e production -s railway-llama-cpp   python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='unsloth/Meta-Llama-3.1-8B-Instruct-GGUF', allow_patterns='*.gguf', local_dir='/opt/models/.cache/huggingface')"
```

For private repos, set `HF_TOKEN` as an environment variable in your Railway project first (not needed for public repos). If the auto-fetch approach would delay your build by many minutes, you can manually download and upload instead.

## Connecting from Open WebUI

This server pairs perfectly with Open WebUI or any OpenAI-compatible UI:

1. In Open WebUI settings, set `OPENAI_API_BASE_URL` to your LLaMA.cpp service URL
2. Example: `http://llama-cpp.railway.internal:8000/v1`
3. Set `DEFAULT_MODELS` to your loaded model's filename (without `.gguf`)

## Why Deploy LLaMA.cpp on Railway

- **Privacy-first** — All inference stays in your infrastructure
- **Cost-effective** — Hobby tier handles small models adequately
- **Fast iteration** — No need to pull full Ollama images or manage model registries
- **Universal compatibility** — Any tool expecting OpenAI endpoints works immediately

## Resources

- [llama-cpp-python Documentation](https://github.com/abetlen/llama-cpp-python)
- [GGUF Model Format](https://github.com/ggml-org/gguf)
- [Railway Docs](https://docs.railway.com)