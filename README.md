# NYT Mini Crosswords MVP

This repo is a small, reviewable MVP for generating 5x5 mini-style crosswords.

## What is in scope
- A Python API that generates crossword grids from a seeded template search.
- A simple React frontend that submits a request and renders the response.
- A template library instead of fully free-form black-square generation.
- Deterministic runs via seed input.
- Timeout responses as a first-class outcome.
- Batched clue generation via the local OpenClaw CLI after a puzzle is solved.

## Repo layout
- `backend/`: FastAPI app, solver, template library, lexicon, tests.
- `frontend/`: Vite + React UI.

## Local development
Backend:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
uvicorn nyt_mini_crosswords.app:app --reload --port 8790
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
pytest
```

## Benchmarking

The solver keeps candidate caching on by default. You can compare it against the uncached baseline with:

Examples:

```bash
cd backend
python scripts/generate_report.py --label baseline --no-candidate-cache --start-seed 1 --count 20
python scripts/generate_report.py --label cached --candidate-cache --start-seed 1 --count 20
python scripts/compare_optimizations.py --start-seed 1 --count 20
```

## Deployment notes
- The frontend build is intended for `/nyt-mini-crosswords/`.
- The backend API is intended to live at `/nyt-mini-crosswords/api/*`.
- Caddy is configured directly in `/etc/caddy/Caddyfile`.
