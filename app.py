"""
Standalone llama.cpp inference server with OpenAI-compatible API endpoint.
Built on llama-cpp-python for minimal resource footprint on Railway.
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import llama_cpp

app = FastAPI(title="llama.cpp Inference Server", version="1.0.0")

# Global model state
model = None
model_path: Optional[str] = None


class CompletionRequest(BaseModel):
    model: str = "default"
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    stop: Optional[List[str]] = None
    stream: bool = False
    echo: bool = False


class EmbeddingRequest(BaseModel):
    input: str
    model: str = "default"


def get_model():
    """Load model from MODEL_PATH environment variable."""
    global model, model_path
    
    if model is not None:
        return model
    
    model_path = os.getenv("MODEL_PATH", "/opt/models/.cache/huggingface")
    model_dir = Path(model_path)
    
    if not model_dir.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Model directory not found: {model_path}. Mount models via volume."
        )
    
    # Find .gguf files in the model directory
    gguf_files = list(model_dir.glob("*.gguf")) + list(model_dir.rglob("*.gguf"))
    
    if not gguf_files:
        raise HTTPException(
            status_code=503,
            detail=f"No .gguf model files found in {model_path}. Please mount a model."
        )
    
    # Use first found model (or you could use MODEL_NAME to specify)
    model_file = gguf_files[0]
    
    # Load with llama-cpp-python
    n_ctx = int(os.getenv("N_CTX", "4096"))
    n_threads = int(os.getenv("N_THREADS", "4"))
    
    model = llama_cpp.Llama(
        model_path=str(model_file),
        n_ctx=n_ctx,
        n_threads=n_threads,
        n_gpu_layers=0,  # Set to >0 if using CUDA/GPU
        verbose=False
    )
    
    return model


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "model_loaded": model is not None}


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "name": "llama.cpp Inference Server",
        "version": "1.0.0",
        "endpoints": ["/v1/completions", "/v1/chat/completions", "/v1/models", "/health"]
    }


@app.get("/v1/models")
async def list_models():
    """List available models (from mounted GGUF files)."""
    model_path = os.getenv("MODEL_PATH", "/opt/models/.cache/huggingface")
    model_dir = Path(model_path)
    
    models = []
    if model_dir.exists():
        gguf_files = list(model_dir.glob("*.gguf")) + list(model_dir.rglob("*.gguf"))
        for f in gguf_files:
            models.append({"id": f.stem, "object": "model", "owned_by": "organization-owner"})
    
    return {"object": "list", "data": models}


@app.post("/v1/completions")
async def completions(request: CompletionRequest):
    """OpenAI-compatible completions endpoint."""
    try:
        llm = get_model()
    except HTTPException as e:
        return {"error": {"message": str(e.detail), "code": 503}}
    
    if request.stream:
        def stream_generator():
            output = llm(
                request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop,
                echo=request.echo,
                stream=True
            )
            for token in output:
                yield f"data: {token['token']}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(stream_generator(), media_type="text/plain")
    
    output = llm(
        request.prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        stop=request.stop,
        echo=request.echo
    )
    
    return {
        "id": "cmpl-default",
        "object": "text_completion",
        "choices": [{"text": output["choices"][0]["text"], "index": 0, "finish_reason": "stop"}],
        "model": request.model
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: dict):
    """OpenAI-compatible chat completions endpoint."""
    # Convert chat format to prompt
    try:
        llm = get_model()
    except HTTPException as e:
        return {"error": {"message": str(e.detail), "code": 503}}
    
    messages = request.get("messages", [])
    model_name = request.get("model", "default")
    
    # Simple prompt conversion (in production, use proper chat template)
    prompt = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            prompt += f"SYSTEM: {content}\n"
        elif role == "user":
            prompt += f"USER: {content}\n"
        elif role == "assistant":
            prompt += f"ASSISTANT: {content}\n"
    prompt += "ASSISTANT: "
    
    output = llm(
        prompt,
        max_tokens=request.get("max_tokens", 512),
        temperature=request.get("temperature", 0.7),
        top_p=request.get("top_p", 0.9),
        stop=request.get("stop"),
        stream=request.get("stream", False)
    )
    
    return {
        "id": "chatcmpl-default",
        "object": "chat.completion",
        "choices": [{"message": {"role": "assistant", "content": output["choices"][0]["text"]}, "index": 0, "finish_reason": "stop"}],
        "model": model_name
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)