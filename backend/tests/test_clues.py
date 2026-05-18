from __future__ import annotations

import json

import nyt_mini_crosswords.clues as clues
from nyt_mini_crosswords.models import SlotAnswer


def test_annotate_answers_with_clues_parses_openclaw_output(monkeypatch) -> None:
    monkeypatch.setenv("OPENCLAW_FORCE_CLUES", "1")

    response_payload = {
        "result": {
            "finalAssistantVisibleText": json.dumps(
                {
                    "clues": [
                        {
                            "slot_id": "slot-1",
                            "clue": "Compass point opposite south",
                        },
                        {
                            "slot_id": "slot-2",
                            "clue": "A common greeting",
                        },
                    ]
                }
            )
        }
    }

    class FakeCompletedProcess:
        returncode = 0
        stdout = json.dumps(response_payload)
        stderr = ""

    def fake_run(*args, **kwargs):
        return FakeCompletedProcess()

    monkeypatch.setattr(clues.subprocess, "run", fake_run)

    answers = [
        SlotAnswer(slot_id="slot-1", direction="across", row=0, col=0, length=5, word="NORTH"),
        SlotAnswer(slot_id="slot-2", direction="down", row=0, col=1, length=5, word="HELLO"),
    ]
    updated, message = clues.annotate_answers_with_clues(answers)

    assert message is None
    assert [answer.clue for answer in updated] == [
        "Compass point opposite south",
        "A common greeting",
    ]
