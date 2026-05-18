from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    seed: int | str | None = Field(default=None, description="Deterministic seed for the run")
    time_budget_ms: int = Field(default=350, ge=25, le=10_000)
    candidate_limit: int = Field(default=48, ge=4, le=256)
    max_search_nodes: int = Field(default=4_000, ge=25, le=100_000)
    template_id: str | None = Field(default=None, description="Optional exact template id")


class SlotAnswer(BaseModel):
    slot_id: str
    direction: Literal["across", "down"]
    row: int
    col: int
    length: int
    word: str


class TemplateInfo(BaseModel):
    id: str
    block_count: int
    rows: list[str]


class GenerationStats(BaseModel):
    elapsed_ms: int
    templates_tried: int
    search_nodes: int
    backtracks: int
    dead_ends: int
    candidate_checks: int


class GenerateResponse(BaseModel):
    status: Literal["ok", "timeout"]
    seed: int
    template: TemplateInfo | None = None
    rows: list[str] | None = None
    answers: list[SlotAnswer] = Field(default_factory=list)
    stats: GenerationStats
    message: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]
    templates: int
    lexicon_size: int
