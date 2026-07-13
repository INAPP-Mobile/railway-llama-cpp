# Deploy and Host

Deploy a private, OpenAI-compatible LLM inference server on Railway in minutes. Drop GGUF-format models into a persistent volume and instantly serve chat completions, text completions, and embeddings through standard OpenAI API endpoints — no GPU, no API keys from third parties, no data leaving your infrastructure.

## About Hosting

LLaMA.cpp runs as a single Docker container using [llama-cpp-python](https://github.com/abetlen/llama-cpp-python), optimized for Railway's Hobby tier with a ~50–200 MB baseline RAM footprint. Models live in a persistent Railway volume and load lazily on the first request, so builds stay fast and redeploys never re-download your weights. The server exposes OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/completions`, `/v1/models`, `/v1/embeddings`) that work as a drop-in backend for OpenAI SDKs, LangChain, and any ChatGPT-style UI.

## Why Deploy

- **No GPU required** — runs entirely on CPU with multi-threaded inference (Railway has no GPU instances)
- **OpenAI-compatible** — point any OpenAI client, SDK, or UI at your instance and it just works
- **Privacy-first** — all inference stays in your Railway project; nothing is sent to external LLM providers
- **Cost-effective** — Hobby tier handles small-to-mid models (up to ~7B params) comfortably
- **Fast startup** — model loads on first request, not at build time; ~10–30 seconds to first token
- **Small image** — ~300 MB vs 2–5 GB for full Ollama images
- **Hugging Face integration** — `huggingface_hub` pre-installed; pull GGUF models with one `MODEL_REPO_ID` env var

## Common Use Cases

- Private ChatGPT-like chat API for personal or team use
- Backend LLM endpoint for AI-powered apps, bots, and workflows
- Embedding generation for RAG pipelines and semantic search
- Model evaluation and prompt-engineering playground
- Paired with Open WebUI for a full self-hosted AI chat interface
- Local GGUF model serving for development and prototyping

## Dependencies for LLaMA.cpp

### Deployment Dependencies

- A Railway account (free Hobby tier works for small models)
- GGUF-format model file(s) — download from Hugging Face Hub or mount an existing volume

### Optional Dependencies

- `HF_TOKEN` — only needed to pull from **private** Hugging Face repos
