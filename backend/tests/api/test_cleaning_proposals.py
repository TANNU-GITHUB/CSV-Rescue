from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sample_missing_and_duplicate_proposals_are_actionable():
    sample = client.post("/api/v1/sessions/sample", json={"sample": "students"})
    assert sample.status_code == 200
    sid = sample.json()["session_id"]

    proposals = client.get(f"/api/v1/sessions/{sid}/proposals").json()["items"]
    missing = next(p for p in proposals if p["action"] == "fill_missing" and p["column"] == "Age")
    assert missing["cells_affected"] > 0
    assert missing["params"]["strategy"] == "mode"

    changed = client.patch(
        f"/api/v1/sessions/{sid}/proposals/{missing['key']}",
        json={"params": {"strategy": "constant", "constant": "18"}},
    )
    assert changed.status_code == 200

    changes = client.get(
        f"/api/v1/sessions/{sid}/proposals/{missing['key']}/changes?limit=20"
    ).json()["items"]
    assert changes
    assert all(change["after"] == "18" for change in changes)

    duplicate = next(p for p in proposals if p["action"] == "remove_duplicate_rows")
    duplicate_changes = client.get(
        f"/api/v1/sessions/{sid}/proposals/{duplicate['key']}/changes?limit=5"
    ).json()["items"]
    assert duplicate_changes
    assert duplicate_changes[0]["kind"] == "row_delete"
    assert duplicate_changes[0]["row"]


def test_duplicate_row_proposal_can_be_accepted_and_undone():
    sample = client.post("/api/v1/sessions/sample", json={"sample": "students"})
    assert sample.status_code == 200
    sid = sample.json()["session_id"]
    duplicate = next(
        p
        for p in client.get(f"/api/v1/sessions/{sid}/proposals").json()["items"]
        if p["action"] == "remove_duplicate_rows"
    )
    changes = client.get(
        f"/api/v1/sessions/{sid}/proposals/{duplicate['key']}/changes"
    ).json()["items"]
    assert changes

    rejected = client.post(
        f"/api/v1/sessions/{sid}/proposals/{duplicate['key']}/apply",
        json={"change_ids": [change["id"] for change in changes]},
    )
    assert rejected.status_code == 400
    assert client.get(f"/api/v1/sessions/{sid}/profile").json()["rows"] == 601

    applied = client.post(
        f"/api/v1/sessions/{sid}/proposals/{duplicate['key']}/apply",
        json={
            "change_ids": [change["id"] for change in changes],
            "confirm_destructive": True,
        },
    )
    assert applied.status_code == 200
    assert applied.json()["op"]["rows_deleted"] == len(changes)
    assert client.get(f"/api/v1/sessions/{sid}/profile").json()["rows"] == 600

    undone = client.post(f"/api/v1/sessions/{sid}/undo")
    assert undone.status_code == 200
    assert undone.json()["session"]["n_rows"] == 601


def test_custom_column_rule_creates_studio_corrections():
    sample = client.post("/api/v1/sessions/sample", json={"sample": "students"})
    sid = sample.json()["session_id"]

    tested = client.post(
        f"/api/v1/sessions/{sid}/rules/test",
        json={
            "type": "range",
            "name": "Age must be at least 18",
            "column": "Age",
            "min": 18,
            "max": 120,
        },
    )
    assert tested.status_code == 200
    assert tested.json()["violations"] > 0

    saved = client.post(
        f"/api/v1/sessions/{sid}/rules",
        json={
            "type": "range",
            "name": "Age must be at least 18",
            "column": "Age",
            "min": 18,
            "max": 120,
        },
    )
    assert saved.status_code == 200

    proposals = client.get(f"/api/v1/sessions/{sid}/proposals").json()["items"]
    correction = next(p for p in proposals if p["action"] == "fix_out_of_range")
    changes = client.get(
        f"/api/v1/sessions/{sid}/proposals/{correction['key']}/changes?limit=20"
    ).json()["items"]
    assert changes

    applied = client.post(
        f"/api/v1/sessions/{sid}/proposals/{correction['key']}/apply",
        json={},
    )
    assert applied.status_code == 200
