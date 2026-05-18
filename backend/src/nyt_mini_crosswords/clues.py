from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from .models import SlotAnswer

LOGGER = logging.getLogger(__name__)
DEFAULT_OPENCLAW_TIMEOUT_SECONDS = 30
DEFAULT_SUBPROCESS_TIMEOUT_SECONDS = DEFAULT_OPENCLAW_TIMEOUT_SECONDS + 15
CLUE_CHUNK_SIZE = max(1, int(os.environ.get("OPENCLAW_CLUE_CHUNK_SIZE", "4")))
CLUE_THINKING = os.environ.get("OPENCLAW_CLUE_THINKING", "minimal")


def annotate_answers_with_clues(answers: Sequence[SlotAnswer]) -> tuple[list[SlotAnswer], str | None]:
    if not answers:
        return [answer.model_copy() for answer in answers], None
    if _should_skip_clues():
        return [answer.model_copy() for answer in answers], None

    updated: list[SlotAnswer] = []
    messages: list[str] = []
    for chunk in _chunk_answers(answers):
        try:
            clue_map = _generate_clue_map(chunk)
        except Exception as exc:  # pragma: no cover - defensive logging path
            LOGGER.warning('Clue generation failed for batch of %s: %s', len(chunk), exc)
            messages.append(f'clue batch of {len(chunk)} failed: {exc}')
            updated.extend(answer.model_copy(update={'clue': None}) for answer in chunk)
            continue

        missing = []
        for answer in chunk:
            clue = clue_map.get(answer.slot_id)
            if clue is None:
                missing.append(answer.slot_id)
            updated.append(answer.model_copy(update={'clue': clue}))

        if missing:
            messages.append(f'clues were not generated for {len(missing)} slot(s) in a batch')

    if messages:
        return updated, 'Clue generation incomplete: ' + '; '.join(messages)
    return updated, None


def _should_skip_clues() -> bool:
    return bool(os.environ.get('PYTEST_CURRENT_TEST')) and not os.environ.get('OPENCLAW_FORCE_CLUES')


def _generate_clue_map(answers: Sequence[SlotAnswer]) -> dict[str, str]:
    command = _resolve_openclaw_command()
    prompt = _build_prompt(answers)
    completed = subprocess.run(
        [
            command,
            '--no-color',
            'agent',
            '--agent',
            'main',
            '--message',
            prompt,
            '--json',
            '--thinking',
            CLUE_THINKING,
            '--timeout',
            str(DEFAULT_OPENCLAW_TIMEOUT_SECONDS),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=DEFAULT_SUBPROCESS_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        raise RuntimeError(
            f'openclaw exited with status {completed.returncode}'
            + (f': {stderr}' if stderr else ''),
        )

    wrapper = json.loads(completed.stdout)
    assistant_text = _extract_assistant_text(wrapper)
    payload = json.loads(assistant_text)
    clues = payload.get('clues')
    if not isinstance(clues, list):
        raise RuntimeError('clue response did not contain a clues array')

    clue_map: dict[str, str] = {}
    for item in clues:
        if not isinstance(item, dict):
            continue
        slot_id = item.get('slot_id')
        clue = item.get('clue')
        if isinstance(slot_id, str) and isinstance(clue, str) and clue.strip():
            clue_map[slot_id] = clue.strip()
    return clue_map


def _build_prompt(answers: Sequence[SlotAnswer]) -> str:
    payload = {
        'task': 'Write concise, fair NYT Mini crossword clues.',
        'output_schema': {
            'clues': [
                {
                    'slot_id': 'string',
                    'clue': 'string',
                }
            ],
        },
        'rules': [
            'Return exactly one JSON object and no prose.',
            'Use the same slot_id values in the output as in the input.',
            'Return one clue per input item, preserving input order.',
            'Keep clues fair, natural, and concise.',
            'Do not repeat the answer verbatim in the clue.',
            'Prefer standard crossword clue style.',
        ],
        'entries': [
            {
                'slot_id': answer.slot_id,
                'answer': answer.word,
                'direction': answer.direction,
                'length': answer.length,
            }
            for answer in answers
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _extract_assistant_text(wrapper: object) -> str:
    if not isinstance(wrapper, dict):
        raise RuntimeError('unexpected openclaw response shape')
    result = wrapper.get('result')
    if not isinstance(result, dict):
        raise RuntimeError('openclaw response missing result field')
    visible = result.get('finalAssistantVisibleText')
    if isinstance(visible, str) and visible.strip():
        return visible
    payloads = result.get('payloads')
    if isinstance(payloads, list) and payloads:
        first = payloads[0]
        if isinstance(first, dict):
            text = first.get('text')
            if isinstance(text, str) and text.strip():
                return text
    raise RuntimeError('openclaw response did not include assistant text')


def _chunk_answers(answers: Sequence[SlotAnswer]) -> list[list[SlotAnswer]]:
    return [list(answers[index : index + CLUE_CHUNK_SIZE]) for index in range(0, len(answers), CLUE_CHUNK_SIZE)]


def _resolve_openclaw_command() -> str:
    command = shutil.which('openclaw')
    if command:
        return command
    fallback = '/home/mainuser/.npm-global/bin/openclaw'
    if Path(fallback).exists():
        return fallback
    raise RuntimeError('openclaw command not found')
