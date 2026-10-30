from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(parents=True, exist_ok=True)


def main() -> None:
    payload = {
        "generated": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "arms": [
            {"name": "Naive auto-clean", "precision": 0.61, "recall": 0.70, "false_correction": 0.09},
            {"name": "CSV Rescue defaults", "precision": 0.89, "recall": 0.92, "false_correction": 0.02},
            {"name": "CSV Rescue + careful review", "precision": 0.98, "recall": 0.91, "false_correction": 0.0},
        ],
        "note": "Placeholder until a full nightly run is wired. Re-run via POST /benchmark/run.",
    }
    (RESULTS / "latest.json").write_text(json.dumps(payload, indent=2))
    print("wrote", RESULTS / "latest.json")


if __name__ == "__main__":
    main()
