from __future__ import annotations

import json
import time

import httpx
from fastapi import APIRouter

from app.config import settings
from app.core.pipeline import detect_current
from app.errors import AppError
from app.llm.providers import groq as groq_provider
from app.llm.service import chat, explain, review_cluster, summarize
from app.llm.service import status as llm_status

router = APIRouter()


@router.get("/ai/status")
def status():
    return llm_status()


@router.get("/ai/models")
def models():
    return {"groq": [settings.GROQ_MODEL], "ollama": [settings.OLLAMA_MODEL]}


@router.post("/ai/chat")
async def chat_ep(body: dict):
    question = body.get("message")
    if not isinstance(question, str) or not question.strip():
        raise AppError("VALIDATION_ERROR", "Write a message for the assistant.", "")
    if len(question) > 2000:
        raise AppError("VALIDATION_ERROR", "That message is too long.", "Keep it under 2,000 characters.")
    history = body.get("history") or []
    if not isinstance(history, list):
        raise AppError("VALIDATION_ERROR", "Conversation history must be a list.", "")
    if any(
        not isinstance(item, dict)
        or item.get("role") not in {"user", "assistant"}
        or not isinstance(item.get("content"), str)
        for item in history
    ):
        raise AppError("VALIDATION_ERROR", "Conversation messages have an invalid format.", "")
    context = body.get("context") or {}
    if not isinstance(context, dict):
        raise AppError("VALIDATION_ERROR", "Assistant context must be an object.", "")
    if len(json.dumps(context, ensure_ascii=False)) > 5000:
        raise AppError("VALIDATION_ERROR", "Assistant context is too large.", "")
    return await chat(question.strip(), history=history, context=context)


@router.post("/ai/test")
async def test(body: dict):
    if body.get("provider") != "groq":
        return {"ok": True, "provider": body.get("provider", "template"), "note": "No external connection is required."}
    if not settings.GROQ_API_KEY:
        return {
            "ok": False,
            "provider": "groq",
            "error": "No Groq API key is configured. Add GROQ_API_KEY to backend/.env and restart the backend.",
        }

    started = time.perf_counter()
    try:
        await groq_provider.complete(
            [{"role": "user", "content": 'Reply with the JSON object {"ok": true}.'}],
            settings.LLM_TIMEOUT_SECONDS,
        )
    except RuntimeError as exc:
        errors = {
            "groq_not_configured": "No Groq API key is configured.",
            "groq_misconfigured": "Groq rejected the API key. Check that the key is valid.",
            "groq_rate_limited": "Groq rate-limited the test. Try again shortly.",
        }
        return {"ok": False, "provider": "groq", "error": errors.get(str(exc), "Groq connection failed.")}
    except httpx.TimeoutException:
        return {"ok": False, "provider": "groq", "error": "Groq did not respond before the timeout. Try again."}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return {
                "ok": False,
                "provider": "groq",
                "error": "Groq could not find the model or endpoint. Check GROQ_MODEL and GROQ_BASE_URL.",
            }
        return {"ok": False, "provider": "groq", "error": f"Groq returned HTTP {exc.response.status_code}."}
    except httpx.RequestError:
        return {
            "ok": False,
            "provider": "groq",
            "error": "Could not reach Groq. Check the backend's network connection.",
        }
    return {
        "ok": True,
        "provider": "groq",
        "model": settings.GROQ_MODEL,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "message": "Groq connection succeeded.",
    }


@router.post("/sessions/{sid}/ai/explain")
async def explain_ep(sid: str, body: dict):
    groups, _ = detect_current(sid)
    key = body.get("issue_key")
    g = next((x for x in groups if x.key == key), None)
    issue = g.model_dump() if g else body
    return await explain(issue, body.get("mode", "auto"))


@router.post("/sessions/{sid}/ai/review-cluster")
async def cluster(sid: str, body: dict):
    return await review_cluster(body.get("values") or [], body.get("column") or "", body.get("mode", "auto"))


@router.post("/sessions/{sid}/ai/summarize")
async def sum_ep(sid: str, body: dict):
    from app.api.verify import latest

    result = (latest(sid) or {}).get("result") or body
    return await summarize(result, body.get("mode", "auto"))
