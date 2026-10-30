# CSV Rescue

Explainable, reversible CSV cleaning. Upload a messy spreadsheet, review every proposed change, undo mistakes, verify, and export a clean file plus a quality report.

The core engine is **100% deterministic** (Pandas / NumPy / RapidFuzz). It works with **no API key and no internet**. An optional LLM layer (Groq → Ollama → built-in templates) only explains and suggests — it never changes data.

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

Optional: for a local backend, create `backend/.env` and add `GROQ_API_KEY=your_key` using a key from [console.groq.com](https://console.groq.com). Restart the backend, then use **Settings → Test Groq connection** to verify it. Docker Compose reads its environment from the repository-root `.env`. Or run `ollama pull llama3.2:3b`.

## What you can do

1. Upload CSV (or load a bundled messy sample)
2. Profile columns and types
3. Review eight kinds of issues
4. Preview before/after in Cleaning Studio
5. Accept, reject, or skip — including per-cell checkboxes
6. Create and test your own per-column or cross-column rules, then review any resulting fixes
7. Verify (detected vs corrected vs dismissed) and export CSV / HTML report / ZIP

Nothing is changed silently. Every operation is undoable.

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

Deploy with the `render.yaml` blueprint, Railway, or Fly.io. Sessions expire after 24 hours.

## Design

The UI is a soft clay / pastel-lavender dashboard. Tokens live in `frontend/src/styles/tokens.css`. Visual reference: `docs/design-reference/dashboard-reference.png`.
