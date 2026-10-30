from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.config import settings
from app.llm.service import chat
from app.main import app

client = TestClient(app)


def test_groq_connection_test_calls_provider(monkeypatch):
    calls = {}

    async def fake_complete(messages, timeout):
        calls["messages"] = messages
        calls["timeout"] = timeout
        return '{"ok": true}'

    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr("app.api.ai.groq_provider.complete", fake_complete)

    response = client.post("/api/v1/ai/test", json={"provider": "groq"})

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert calls["messages"][0]["role"] == "user"
    assert calls["timeout"] == settings.LLM_TIMEOUT_SECONDS


def test_groq_connection_test_reports_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    response = client.post("/api/v1/ai/test", json={"provider": "groq"})

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "backend/.env" in response.json()["error"]


def test_ai_chat_returns_assistant_answer(monkeypatch):
    async def fake_chat(question, history=None, context=None, mode="auto"):
        assert question == "How do I fix blanks?"
        assert context == {"issue_type": "missing_value"}
        return {"answer": "Review the fill strategy in Cleaning Studio.", "source": "groq"}

    monkeypatch.setattr("app.api.ai.chat", fake_chat)

    response = client.post(
        "/api/v1/ai/chat",
        json={"message": "How do I fix blanks?", "context": {"issue_type": "missing_value"}},
    )

    assert response.status_code == 200
    assert response.json()["answer"].startswith("Review")


def test_ai_chat_rejects_empty_message():
    response = client.post("/api/v1/ai/chat", json={"message": " "})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_ai_chat_uses_plain_text_completion(monkeypatch):
    async def fake_complete_chain(messages, mode, json_mode=True):
        assert json_mode is False
        return "Choose a fill strategy in Cleaning Studio.", "groq", None, 10

    monkeypatch.setattr("app.llm.service.complete_chain", fake_complete_chain)

    result = asyncio.run(chat("How do I fill a missing value?"))

    assert result["source"] == "groq"
    assert "Cleaning Studio" in result["answer"]
