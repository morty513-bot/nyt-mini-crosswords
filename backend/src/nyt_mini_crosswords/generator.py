from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

from .grid import CrosswordState, Slot, Template, extract_slots
from .lexicon import Lexicon, WordEntry
from .models import GenerationStats, GenerateResponse, SlotAnswer, TemplateInfo


class GenerationTimeout(RuntimeError):
    pass


@dataclass(slots=True)
class SolverState:
    template: Template
    slots: list[Slot]
    board: CrosswordState
    assignments: dict[str, str]
    used_words: set[str]


@dataclass(frozen=True, slots=True)
class GenerationOptions:
    candidate_cache: bool = False
    slot_impact_tiebreak: bool = False
    template_scoring: bool = False


@dataclass(frozen=True, slots=True)
class TemplateProfile:
    template: Template
    slots: tuple[Slot, ...]
    slot_count: int
    intersection_count: int


class CrosswordGenerator:
    def __init__(self, lexicon: Lexicon, templates: list[Template], options: GenerationOptions | None = None):
        self.lexicon = lexicon
        self.templates = templates
        self.options = options or GenerationOptions()
        self._template_profiles = [self._build_template_profile(template) for template in templates]

    def generate(
        self,
        seed: int,
        time_budget_ms: int,
        candidate_limit: int,
        max_search_nodes: int,
        template_id: str | None = None,
        options: GenerationOptions | None = None,
    ) -> GenerateResponse:
        start = time.perf_counter()
        deadline = start + time_budget_ms / 1000.0
        rng = random.Random(seed)
        stats = _Stats()
        resolved_options = options or self.options
        templates = list(self._template_profiles)
        if template_id is not None:
            matching = [profile for profile in templates if profile.template.template_id == template_id]
            templates = matching or templates
        if resolved_options.template_scoring:
            templates.sort(
                key=lambda profile: (
                    _template_priority(profile.template.block_count),
                    profile.slot_count,
                    -profile.intersection_count,
                    rng.random(),
                ),
            )
        else:
            templates.sort(key=lambda profile: (_template_priority(profile.template.block_count), rng.random()))
        last_state: SolverState | None = None
        max_attempts = min(6, len(templates))
        if max_attempts <= 0:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return self._timeout_response(seed, None, stats, elapsed_ms, message="No crossword templates were available.")
        template_time_slice_ms = max(50, time_budget_ms // max_attempts)
        template_node_slice = max(250, max_search_nodes // max_attempts)
        for profile in templates[:max_attempts]:
            if time.perf_counter() > deadline:
                break
            stats.templates_tried += 1
            state = SolverState(
                template=profile.template,
                slots=list(profile.slots),
                board=CrosswordState(profile.template),
                assignments={},
                used_words=set(),
            )
            last_state = state
            try:
                template_deadline = min(deadline, time.perf_counter() + template_time_slice_ms / 1000.0)
                if self._solve(state, rng, template_deadline, candidate_limit, template_node_slice, stats, resolved_options):
                    elapsed_ms = int((time.perf_counter() - start) * 1000)
                    return self._success_response(seed, state, stats, elapsed_ms)
            except GenerationTimeout:
                continue
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return self._timeout_response(seed, last_state, stats, elapsed_ms, message="No template could be solved within the time budget.")

    def _success_response(self, seed: int, state: SolverState, stats: "_Stats", elapsed_ms: int) -> GenerateResponse:
        answers = [
            SlotAnswer(
                slot_id=slot.slot_id,
                direction=slot.direction,
                row=slot.row,
                col=slot.col,
                length=slot.length,
                word=state.assignments[slot.slot_id],
            )
            for slot in state.slots
        ]
        template = TemplateInfo(id=state.template.template_id, block_count=state.template.block_count, rows=list(state.template.rows))
        return GenerateResponse(
            status="ok",
            seed=seed,
            template=template,
            rows=state.board.render(),
            answers=answers,
            stats=GenerationStats(
                elapsed_ms=elapsed_ms,
                templates_tried=stats.templates_tried,
                search_nodes=stats.search_nodes,
                backtracks=stats.backtracks,
                dead_ends=stats.dead_ends,
                candidate_checks=stats.candidate_checks,
            ),
        )

    def _timeout_response(
        self,
        seed: int,
        state: SolverState | None,
        stats: "_Stats",
        elapsed_ms: int,
        message: str | None = None,
    ) -> GenerateResponse:
        template = None if state is None else TemplateInfo(id=state.template.template_id, block_count=state.template.block_count, rows=list(state.template.rows))
        rows = None if state is None else state.board.render()
        return GenerateResponse(
            status="timeout",
            seed=seed,
            template=template,
            rows=rows,
            answers=[],
            stats=GenerationStats(
                elapsed_ms=elapsed_ms,
                templates_tried=stats.templates_tried,
                search_nodes=stats.search_nodes,
                backtracks=stats.backtracks,
                dead_ends=stats.dead_ends,
                candidate_checks=stats.candidate_checks,
            ),
            message=message or "Generation timed out before a complete fill was found.",
        )

    def _solve(
        self,
        state: SolverState,
        rng: random.Random,
        deadline: float,
        candidate_limit: int,
        max_search_nodes: int,
        stats: "_Stats",
        options: GenerationOptions,
    ) -> bool:
        if time.perf_counter() > deadline:
            raise GenerationTimeout()
        if stats.search_nodes >= max_search_nodes:
            raise GenerationTimeout()
        if len(state.assignments) == len(state.slots):
            return True

        slot, candidates = self._choose_slot(state, rng, candidate_limit, stats, options)
        if slot is None:
            return False
        if not candidates:
            stats.dead_ends += 1
            return False

        for entry in candidates:
            stats.search_nodes += 1
            if time.perf_counter() > deadline or stats.search_nodes >= max_search_nodes:
                raise GenerationTimeout()
            if entry.word in state.used_words:
                continue
            if not state.board.can_place(slot, entry.word):
                continue
            changes = state.board.place(slot, entry.word)
            state.assignments[slot.slot_id] = entry.word
            state.used_words.add(entry.word)
            if self._forward_check(state, rng, candidate_limit, stats, options):
                if self._solve(state, rng, deadline, candidate_limit, max_search_nodes, stats, options):
                    return True
            stats.backtracks += 1
            state.used_words.remove(entry.word)
            del state.assignments[slot.slot_id]
            state.board.undo(changes)
        stats.dead_ends += 1
        return False

    def _choose_slot(
        self,
        state: SolverState,
        rng: random.Random,
        candidate_limit: int,
        stats: "_Stats",
        options: GenerationOptions,
    ) -> tuple[Slot | None, list[WordEntry]]:
        best_slot: Slot | None = None
        best_candidates: list[WordEntry] = []
        best_score: tuple[float, float, float] = (math.inf, math.inf, math.inf)
        remaining = [slot for slot in state.slots if slot.slot_id not in state.assignments]
        slot_impact: dict[str, int] = {}
        if options.slot_impact_tiebreak:
            slot_impact = self._slot_impact_scores(remaining)
        else:
            rng.shuffle(remaining)
        for slot in remaining:
            pattern = state.board.pattern_for_slot(slot)
            candidates = self.lexicon.candidates(
                slot.length,
                pattern,
                state.used_words,
                candidate_limit,
                use_cache=options.candidate_cache,
            )
            stats.candidate_checks += 1
            if not candidates:
                return slot, []
            impact_score = float(slot_impact.get(slot.slot_id, 0)) if options.slot_impact_tiebreak else 0.0
            score = (float(len(candidates)), -impact_score, rng.random())
            if score < best_score:
                best_slot = slot
                best_candidates = candidates
                best_score = score
                if not options.slot_impact_tiebreak and len(candidates) == 1:
                    break
        if best_slot is None:
            return None, []
        weighted = [
            (entry.weight + rng.random() * 0.01, entry)
            for entry in best_candidates
        ]
        weighted.sort(key=lambda item: (-item[0], item[1].word))
        return best_slot, [entry for _, entry in weighted]

    def _forward_check(
        self,
        state: SolverState,
        rng: random.Random,
        candidate_limit: int,
        stats: "_Stats",
        options: GenerationOptions,
    ) -> bool:
        for slot in state.slots:
            if slot.slot_id in state.assignments:
                continue
            pattern = state.board.pattern_for_slot(slot)
            candidates = self.lexicon.candidates(
                slot.length,
                pattern,
                state.used_words,
                candidate_limit,
                use_cache=options.candidate_cache,
            )
            stats.candidate_checks += 1
            if not candidates:
                return False
        return True

    def _slot_impact_scores(self, remaining: list[Slot]) -> dict[str, int]:
        cell_to_slots: dict[tuple[int, int], set[str]] = {}
        for slot in remaining:
            for cell in slot.cells:
                cell_to_slots.setdefault(cell, set()).add(slot.slot_id)
        scores: dict[str, int] = {}
        for slot in remaining:
            impacted: set[str] = set()
            for cell in slot.cells:
                for other in cell_to_slots.get(cell, set()):
                    if other != slot.slot_id:
                        impacted.add(other)
            scores[slot.slot_id] = len(impacted)
        return scores

    def _build_template_profile(self, template: Template) -> TemplateProfile:
        slots = tuple(extract_slots(template))
        intersections: dict[tuple[int, int], int] = {}
        for slot in slots:
            for cell in slot.cells:
                intersections[cell] = intersections.get(cell, 0) + 1
        intersection_count = sum(1 for count in intersections.values() if count > 1)
        return TemplateProfile(
            template=template,
            slots=slots,
            slot_count=len(slots),
            intersection_count=intersection_count,
        )


@dataclass(slots=True)
class _Stats:
    templates_tried: int = 0
    search_nodes: int = 0
    backtracks: int = 0
    dead_ends: int = 0
    candidate_checks: int = 0


def _template_priority(block_count: int) -> int:
    if block_count == 4:
        return 0
    if block_count == 5:
        return 1
    if block_count == 3:
        return 2
    if block_count == 2:
        return 3
    if block_count == 1:
        return 4
    return 5
