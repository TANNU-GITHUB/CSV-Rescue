from __future__ import annotations

import httpx

from app.config import settings


async def complete(messages: list[dict], timeout: int, json_mode: bool = True) -> str:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("groq_not_configured")
    url = settings.GROQ_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    body = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 500,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=body, headers=headers)
        if r.status_code in (401, 403):
            raise RuntimeError("groq_misconfigured")
        if r.status_code == 429:
            raise RuntimeError("groq_rate_limited")
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
