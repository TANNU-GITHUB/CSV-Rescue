# CSV Rescue

CSV Rescue helps people clean and validate messy CSV files without losing control of their data. It identifies common data-quality problems, explains them, and proposes corrections that users can inspect before applying. Changes are reversible, so users can undo an accepted operation.

## The problem it solves

Cleaning a spreadsheet by hand is slow and error-prone. Missing values, duplicate rows, inconsistent formats, invalid numbers, and other issues can be difficult to find across a large file. Automated tools can also make it hard to understand what was changed or restore the original data.

CSV Rescue makes this workflow reviewable: it profiles a dataset, groups detected issues, shows proposed changes with their reasons, and lets the user accept, reject, or skip each proposal. It also supports custom validation rules and produces verification results and exportable reports.

## What it does

Upload a CSV or open a bundled sample to profile its columns and detect data-quality issues. Review proposed corrections in Cleaning Studio, including the affected cells or rows, then decide which changes to apply. After cleaning, verify the dataset and export the corrected CSV and a quality report.

The core cleaning and validation engine is deterministic (Pandas, NumPy, and RapidFuzz) and works without an API key or internet connection. Optional AI assistance can explain issues and answer questions, but it does not apply data changes.

## Features

- **Dataset profiling:** inspect row and column counts, inferred column types, missing cells, duplicates, and column summaries.
- **Issue detection:** find missing values, duplicate rows and identifiers, inconsistent text and formats, invalid numeric values, invalid values, and outliers.
- **Reviewable corrections:** preview proposed changes before applying them; select individual changes and accept, reject, or skip a proposal.
- **Duplicate and missing-value handling:** review duplicate-row deletions with full row contents, choose which duplicate to keep, and select how missing values should be handled.
- **Custom rules:** define, test, save, and run rules for individual columns or relationships between columns, then review resulting corrections.
- **Undo and history:** reverse accepted cleaning operations and review the operation history.
- **Verification and export:** compare detected, corrected, and dismissed issues; export a cleaned CSV, HTML report, or ZIP bundle.
- **Optional AI help:** use the assistant to ask questions or get explanations. Groq can be configured as a provider; the deterministic cleaning workflow does not require it.


## Quick start

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m app.samples.generate_samples
uvicorn app.main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The API lives at http://localhost:8000/api/v1/health.


## Tests

```bash
cd backend && pytest
cd frontend && npm test -- --run
bash scripts/smoke.sh http://localhost:8000
```

## Docker

```bash
docker compose up --build
```

