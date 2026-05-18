# nyt-mini-crosswords

Single-repo MVP for generating NYT-mini-style crosswords.

## Layout
- `frontend/` is a thin React UI.
- `backend/` owns the generator, lexicon, and API.

## Rules
- Keep generation logic in the backend, not the UI.
- Prefer small, reviewable modules over clever monoliths.
- Preserve deterministic seeding for reproducibility.
- Do not touch the parent workspace files unless explicitly needed for this repo.

## Deployment
- Backend listens on `127.0.0.1:8790`.
- Frontend is built to `frontend/dist` and served by Caddy under `/nyt-mini-crosswords/`.
