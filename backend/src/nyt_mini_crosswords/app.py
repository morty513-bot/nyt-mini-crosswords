from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException

from .clues import annotate_answers_with_clues
from .generator import CrosswordGenerator, GenerationOptions
from .lexicon import Lexicon
from .models import GenerateRequest, GenerateResponse, HealthResponse
from .templates import build_templates

DATA_FILE = Path(__file__).resolve().parent / "data" / "words.tsv"


def _load_lexicon() -> Lexicon:
    return Lexicon.from_tsv(DATA_FILE)


LEXICON = _load_lexicon()
TEMPLATES = build_templates()
GENERATOR = CrosswordGenerator(LEXICON, TEMPLATES)

app = FastAPI(title="NYT Mini Crosswords", version="0.1.0")


@app.get("/api/health", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", templates=len(TEMPLATES), lexicon_size=LEXICON.size)


@app.post("/api/generate", response_model=GenerateResponse)
@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    seed = _seed_value(request.seed)
    if not TEMPLATES:
        raise HTTPException(status_code=500, detail="No crossword templates are available.")
    outcome = GENERATOR.generate(
        seed=seed,
        time_budget_ms=request.time_budget_ms,
        candidate_limit=request.candidate_limit,
        max_search_nodes=request.max_search_nodes,
        template_id=request.template_id,
        options=GenerationOptions(candidate_cache=request.candidate_cache),
    )
    if outcome.status == "ok":
        answers, clue_message = annotate_answers_with_clues(outcome.answers)
        outcome.answers = answers
        outcome.clue_message = clue_message
    return outcome


def _seed_value(value: int | str | None) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except ValueError:
        return abs(hash(value)) % (2**31)
