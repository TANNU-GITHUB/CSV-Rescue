from __future__ import annotations

import time

from app.config import settings
from app.llm.providers import groq as groq_provider
from app.llm.providers import ollama as ollama_provider

_fail: dict[str, tuple[int, float]] = {}


def _blocked(name: str) -> bool:
    rec = _fail.get(name)
    if not rec:
        return False
    n, ts = rec
    if n >= 3 and time.time() - ts < 60:
        return True
    return False


def _mark(name: str, ok: bool) -> None:
    if ok:
        _fail.pop(name, None)
        return
    n, _ = _fail.get(name, (0, 0.0))
    _fail[name] = (n + 1, time.time())


async def complete_chain(
    messages: list[dict],
    mode: str,
    json_mode: bool = True,
) -> tuple[str, str, str | None, int]:
    order = []
    if settings.LLM_ENABLED and mode != "off":
        if mode == "ollama_only":
            order = ["ollama"]
        else:
            order = [p.strip() for p in settings.LLM_PROVIDER_ORDER.split(",") if p.strip()]
    started = time.time()
    last_reason = None
    for name in order:
        if _blocked(name):
            last_reason = f"{name}_circuit_open"
            continue
        try:
            if name == "groq":
                text = await groq_provider.complete(messages, settings.LLM_TIMEOUT_SECONDS, json_mode=json_mode)
            elif name == "ollama":
                text = await ollama_provider.complete(messages, settings.LLM_TIMEOUT_SECONDS)
            else:
                continue
            _mark(name, True)
            return text, name, None, int((time.time() - started) * 1000)
        except Exception as e:
            _mark(name, False)
            last_reason = str(e)[:80]
    return "", "template", last_reason or "no_provider", int((time.time() - started) * 1000)
