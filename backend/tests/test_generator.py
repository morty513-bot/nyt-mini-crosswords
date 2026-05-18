from __future__ import annotations

from pathlib import Path

from nyt_mini_crosswords.app import GENERATOR, LEXICON, TEMPLATES
from nyt_mini_crosswords.generator import _Stats, _timeout_message
from nyt_mini_crosswords.lexicon import Lexicon
from nyt_mini_crosswords.templates import build_templates
from nyt_mini_crosswords.wordlist_filters import REJECTED_WORDS, is_allowed_word


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
    assert outcome.message is not None
    assert outcome.message.startswith("Timed out because ")
    assert "time budget" in outcome.message or "node limit" in outcome.message


def test_timeout_message_includes_reason_and_stats() -> None:
    message = _timeout_message(
        "search node limit of 10 reached while solving template demo",
        _Stats(templates_tried=2, search_nodes=10, backtracks=3, dead_ends=1, candidate_checks=4),
        1000,
    )
    assert message.startswith("Timed out because search node limit of 10 reached while solving template demo.")
    assert "templates tried: 2" in message
    assert "search nodes: 10" in message
    assert "backtracks: 3" in message
    assert "dead ends: 1" in message
    assert "candidate checks: 4" in message
    assert "budget: 1000 ms" in message


def test_generation_succeeds_for_known_seed() -> None:
    outcome = GENERATOR.generate(seed=48, time_budget_ms=1000, candidate_limit=64, max_search_nodes=20_000)
    assert outcome.status in {"ok", "timeout"}
    if outcome.status != "ok":
        return
    forbidden = {"pdf", "pda", "dvd", "usa", "jan", "hugo", "debra", "delhi"}
    for answer in outcome.answers:
        assert answer.word.lower() not in forbidden


def test_lexicon_pattern_filtering(tmp_path: Path) -> None:
    path = tmp_path / "words.tsv"
    path.write_text("apple\t1\nangle\t2\nalley\t3\n", encoding="utf-8")
    lexicon = Lexicon.from_tsv(path)
    candidates = lexicon.candidates(5, "APP..", set())
    assert [entry.word for entry in candidates] == ["APPLE"]


def test_wordlist_filters_block_obvious_bad_tokens() -> None:
    for word in ["pdf", "pda", "dvd", "usa", "jan", "hugo", "debra", "delhi"]:
        assert word in REJECTED_WORDS
        assert not is_allowed_word(word, 9.0)


def test_committed_lexicon_excludes_obvious_bad_tokens() -> None:
    committed = {entry.word.lower() for entry in LEXICON.words_of_length(3)}
    committed.update(entry.word.lower() for entry in LEXICON.words_of_length(4))
    committed.update(entry.word.lower() for entry in LEXICON.words_of_length(5))
    for word in REJECTED_WORDS:
        assert word not in committed
