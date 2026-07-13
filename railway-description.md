# Deploy and Host

Deploy a lightweight, OpenAI-compatible LLM inference server on Railway. Add GGUF-format models to a persistent volume and instantly serve requests via standard OpenAI API endpoints — no GPU required.

## About Hosting

LLaMA.cpp runs as a single Docker container using [llama-cpp-python](https://github.com/abetlen/llama-cpp-python), optimized for Railway's Hobby tier with a ~50–200 MB baseline RAM footprint. Models are stored in a persistent Railway volume and load on first request. The server exposes OpenAI-compatible endpoints (`/v1/completions`, `/v1/chat/completions`, `/v1/models`) that work as a drop-in replacement for any OpenAI client.

## Why Deploy

- **No GPU required** — runs entirely on CPU with multi-threaded inference
- **OpenAI-compatible** — use any tool, library, or UI that speaks the OpenAI API format
- **Privacy-first** — all inference stays on your infrastructure, no data leaves Railway
- **Cost-effective** — Hobby tier handles small models (up to 7B parameters) comfortably
- **Fast startup** — model loads on first request, not at build time; ~10–30 seconds to first token
- **Small image** — ~300 MB image vs 2–5 GB for full Ollama images
- **Hugging Face integration** — `huggingface_hub` pre-installed for one-command model downloads

## Common Use Cases

- Private ChatGPT-like chat API for personal or team use
- Backend LLM endpoint for AI-powered applications and workflows
- Embedding generation service for RAG pipelines
- Model evaluation and testing playground
- Paired with Open WebUI for a complete self-hosted AI chat interface
- Development and prototyping with local GGUF models

## Dependencies

### Deployment Dependencies

- Railway account (free Hobby tier works for small models)
- GGUF-format model files (download from Hugging Face Hub)

### Optional Dependencies

- (Optional) Hugging Face token (`HF_TOKEN`) for downloading from private repos
- (Optional) Railway GPU plugin for CUDA-accelerated inference on Pro tier