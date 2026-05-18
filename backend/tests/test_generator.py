from __future__ import annotations

from pathlib import Path

from nyt_mini_crosswords.app import GENERATOR, LEXICON, TEMPLATES
from nyt_mini_crosswords.lexicon import Lexicon
from nyt_mini_crosswords.templates import build_templates


def test_template_library_is_not_empty() -> None:
    assert TEMPLATES
    assert any(template.block_count <= 6 for template in TEMPLATES)


def test_lexicon_loader_is_ranked() -> None:
    words = LEXICON.words_of_length(5)
    assert words
    assert words[0].weight >= words[-1].weight


def test_generation_produces_only_known_words() -> None:
    outcome = GENERATOR.generate(seed=17, time_budget_ms=500, candidate_limit=64, max_search_nodes=10_000)
    assert outcome.status in {"ok", "timeout"}
    if outcome.status != "ok":
        return
    known_words = {entry.word for entry in LEXICON.words_of_length(3)}
    known_words.update(entry.word for entry in LEXICON.words_of_length(4))
    known_words.update(entry.word for entry in LEXICON.words_of_length(5))
    for answer in outcome.answers:
        assert answer.word in known_words


def test_generation_reports_timeout_for_tiny_budget() -> None:
    outcome = GENERATOR.generate(seed=3, time_budget_ms=0, candidate_limit=8, max_search_nodes=1)
    assert outcome.status == "timeout"


def test_lexicon_pattern_filtering(tmp_path: Path) -> None:
    path = tmp_path / "words.tsv"
    path.write_text("apple\t1\nangle\t2\nalley\t3\n", encoding="utf-8")
    lexicon = Lexicon.from_tsv(path)
    candidates = lexicon.candidates(5, "APP..", set())
    assert [entry.word for entry in candidates] == ["APPLE"]
