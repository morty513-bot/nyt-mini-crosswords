from __future__ import annotations

from nyt_mini_crosswords import sweep


def test_summarize_counts_successes_and_timeouts() -> None:
    records = [
        sweep.SweepRecord(1, "ok", 120, 10, "template-a", None, 200),
        sweep.SweepRecord(2, "timeout", 1000, 0, "template-b", "timed out", 5000),
        sweep.SweepRecord(3, "ok", 240, 10, "template-a", None, 300),
    ]

    summary = sweep.summarize(records)

    assert summary["seeds_run"] == 3
    assert summary["successes"] == 2
    assert summary["timeouts"] == 1
    assert summary["other_failures"] == 0
    assert summary["success_rate"] == 2 / 3
    assert summary["timeout_rate"] == 1 / 3
    assert summary["best_seed"] == 1
    assert summary["worst_seed"] == 3
    assert summary["timeout_seeds"] == [2]


def test_seed_series_is_sequential_with_step() -> None:
    assert sweep.seed_series(10, 4, 3) == [10, 13, 16, 19]
