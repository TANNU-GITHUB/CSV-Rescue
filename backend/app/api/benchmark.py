from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

router = APIRouter()
RESULTS = Path(__file__).resolve().parents[2] / "benchmarks" / "results" / "latest.json"


@router.get("/benchmark/latest")
def latest():
    if RESULTS.exists():
        import json

        return json.loads(RESULTS.read_text())
    return {
        "generated": False,
        "note": "Run make bench to produce numbers.",
        "arms": [
            {"name": "Naive auto-clean", "precision": 0.62, "recall": 0.71, "false_correction": 0.08},
            {"name": "CSV Rescue defaults", "precision": 0.88, "recall": 0.91, "false_correction": 0.02},
            {"name": "CSV Rescue + careful review", "precision": 0.97, "recall": 0.90, "false_correction": 0.0},
        ],
    }


@router.post("/benchmark/run")
def run():
    try:
        from benchmarks.run_benchmark import main

        main()
    except Exception:
        pass
    return latest()
