#!/usr/bin/env python3
"""
Test chat CLI for LLaMA.cpp Inference Server.

Sends a prompt to the deployed llama.cpp server and prints the response.
Useful for quick smoke tests after deploying or updating models.

Usage:
    python test-chat.py --url http://localhost:8000
    python test-chat.py --url https://your-service.up.railway.app --prompt "Tell me a joke"
    python test-chat.py --url http://localhost:8000 --stream
    python test-chat.py --list-models --url https://your-service.up.railway.app
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
import ssl


def list_models(base_url: str) -> list:
    """Fetch available models from /v1/models."""
    url = f"{base_url.rstrip('/')}/v1/models"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=30) as resp:
            data = json.loads(resp.read())
            return [m["id"] for m in data.get("data", [])]
    except urllib.error.HTTPError as e:
        print(f"  [HTTP {e.code}] {e.read().decode(errors='replace')}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"  [ERROR] {e}", file=sys.stderr)
        sys.exit(1)


def health_check(base_url: str) -> dict:
    """Check server health."""
    url = f"{base_url.rstrip('/')}/health"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"status": "error", "error": str(e)}


def send_chat(
    base_url: str,
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 256,
    temperature: float = 0.7,
    stream: bool = False,
):
    """Send a chat completion request and print the response."""
    url = f"{base_url.rstrip('/')}/v1/chat/completions"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    body = json.dumps({
        "model": "default",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }).encode()

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        if stream:
            resp = urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=120)
            print("[streaming] ", end="", flush=True)
            for line in resp:
                line = line.decode(errors="replace").strip()
                if not line:
                    continue
                if line == "data: [DONE]":
                    break
                if line.startswith("data: "):
                    try:
                        chunk = json.loads(line[6:])
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            print(content, end="", flush=True)
                    except json.JSONDecodeError:
                        pass
            print()
        else:
            resp = urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=120)
            data = json.loads(resp.read())
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(content)

    except urllib.error.HTTPError as e:
        print(f"[HTTP {e.code}] {e.read().decode(errors='replace')}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


def send_completion(
    base_url: str,
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.7,
):
    """Send a text completion request."""
    url = f"{base_url.rstrip('/')}/v1/completions"

    body = json.dumps({
        "model": "default",
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=120) as resp:
            data = json.loads(resp.read())
            content = data.get("choices", [{}])[0].get("text", "")
            print(content)
    except urllib.error.HTTPError as e:
        print(f"[HTTP {e.code}] {e.read().decode(errors='replace')}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Test chat CLI for LLaMA.cpp Inference Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--url", "-u",
        default="http://localhost:8000",
        help="Server base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--prompt", "-p",
        default="Hello! What can you do? Please respond in one short sentence.",
        help="Prompt text to send",
    )
    parser.add_argument(
        "--system", "-s",
        default="",
        help="Optional system prompt",
    )
    parser.add_argument(
        "--max-tokens", "-m",
        type=int,
        default=256,
        help="Maximum tokens in response (default: 256)",
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream the response token by token",
    )
    parser.add_argument(
        "--completion",
        action="store_true",
        help="Use /v1/completions endpoint instead of /v1/chat/completions",
    )
    parser.add_argument(
        "--list-models", "-l",
        action="store_true",
        help="List available models and exit",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check server health and exit",
    )

    args = parser.parse_args()

    if args.health:
        status = health_check(args.url)
        print(json.dumps(status, indent=2))
        return

    if args.list_models:
        models = list_models(args.url)
        if models:
            print("Available models:")
            for m in models:
                print(f"  - {m}")
        else:
            print("No models found (no .gguf files mounted)")
        return

    if args.completion:
        send_completion(args.url, args.prompt, args.max_tokens, args.temperature)
    else:
        send_chat(args.url, args.prompt, args.system, args.max_tokens, args.temperature, args.stream)


if __name__ == "__main__":
    main()