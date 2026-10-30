from __future__ import annotations

import httpx

from app.config import settings


async def complete(messages: list[dict], timeout: int) -> str:
    if not settings.OLLAMA_BASE_URL:
        raise RuntimeError("ollama_disabled")
    url = settings.OLLAMA_BASE_URL.rstrip("/") + "/api/chat"
    body = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_predict": 500},
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=body)
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "")
