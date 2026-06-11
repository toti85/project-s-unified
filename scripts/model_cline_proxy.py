"""Loopback-only compatibility proxy for the local Qwen3.6 llama.cpp server."""

import argparse
import json
import re

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse


parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8097)
parser.add_argument("--upstream", default="http://127.0.0.1:8096")
args, _ = parser.parse_known_args()

app = FastAPI(title="Local Model Compatibility Proxy", version="2.0")
think_block = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
think_prefix = re.compile(r"^\s*</think>\s*", re.DOTALL)


def strip_thinking(text: str) -> str:
    if not text:
        return text
    return think_prefix.sub("", think_block.sub("", text)).strip()


def prepare_body(body: dict) -> dict:
    body.setdefault("chat_template_kwargs", {})["enable_thinking"] = False
    body.setdefault("temperature", 0.2)
    return body


@app.get("/v1/models")
async def models():
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{args.upstream}/v1/models")
    return JSONResponse(response.json(), status_code=response.status_code)


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{args.upstream}/health")
        return JSONResponse({"status": "ok", "upstream": response.json()})
    except Exception as exc:
        return JSONResponse({"status": "error", "detail": str(exc)}, status_code=503)


async def filter_stream(response):
    async for line in response.aiter_lines():
        if not line.startswith("data: "):
            if line:
                yield f"{line}\n".encode()
            continue
        payload = line[6:]
        if payload == "[DONE]":
            yield b"data: [DONE]\n\n"
            continue
        data = json.loads(payload)
        for choice in data.get("choices", []):
            delta = choice.get("delta", {})
            delta.pop("reasoning_content", None)
            if delta.get("content"):
                delta["content"] = strip_thinking(delta["content"])
        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode()


@app.post("/v1/chat/completions")
async def chat(request: Request):
    body = prepare_body(await request.json())
    if body.get("stream"):
        async def generate():
            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream("POST", f"{args.upstream}/v1/chat/completions", json=body) as response:
                    async for chunk in filter_stream(response):
                        yield chunk
        return StreamingResponse(generate(), media_type="text/event-stream")

    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(f"{args.upstream}/v1/chat/completions", json=body)
    data = response.json()
    for choice in data.get("choices", []):
        message = choice.get("message", {})
        message["content"] = strip_thinking(message.get("content", ""))
        message.pop("reasoning_content", None)
    return JSONResponse(data, status_code=response.status_code)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=args.port)