from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.samples.generate_samples import main as gen

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_sample_flow():
    gen()
    r = client.post("/api/v1/sessions/sample", json={"sample": "students"})
    assert r.status_code == 200, r.text
    sid = r.json()["session_id"]
    issues = client.get(f"/api/v1/sessions/{sid}/issues").json()["items"]
    assert len(issues) >= 1
    dash = client.get(f"/api/v1/sessions/{sid}/dashboard")
    assert dash.status_code == 200
    client.post(f"/api/v1/sessions/{sid}/proposals/apply-safe")
    v = client.post(f"/api/v1/sessions/{sid}/verify")
    assert v.status_code == 200
    assert v.json()["verdict"] in {"improved", "clean", "not_improved"}
    csv = client.get(f"/api/v1/sessions/{sid}/export/csv")
    assert csv.status_code == 200
    assert len(csv.content) > 0
    d = client.delete(f"/api/v1/sessions/{sid}")
    assert d.status_code == 204


def test_error_envelope_missing_session():
    r = client.get("/api/v1/sessions/does-not-exist")
    assert r.status_code in (404, 410, 400)
    body = r.json()
    assert "error" in body
    assert "code" in body["error"]
