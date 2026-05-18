from __future__ import annotations

import argparse

from nyt_mini_crosswords.generator import GenerationOptions
from nyt_mini_crosswords.report import build_comparison_report, build_report
from nyt_mini_crosswords.sweep import seed_series, sweep_seeds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare crossword generator caching on a fixed seed set.")
    parser.add_argument("--start-seed", type=int, default=1, help="First seed to try.")
    parser.add_argument("--count", type=int, default=50, help="How many sequential seeds to try.")
    parser.add_argument("--step", type=int, default=1, help="Step between seeds.")
    parser.add_argument("--time-budget-ms", type=int, default=1000, help="Per-seed time budget.")
    parser.add_argument("--candidate-limit", type=int, default=64, help="Per-slot candidate cap.")
    parser.add_argument("--max-search-nodes", type=int, default=20_000, help="Per-seed search node limit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seeds = seed_series(args.start_seed, args.count, args.step)
    baseline = sweep_seeds(
        seeds,
        time_budget_ms=args.time_budget_ms,
        candidate_limit=args.candidate_limit,
        max_search_nodes=args.max_search_nodes,
        options=GenerationOptions(candidate_cache=False),
    )
    cached = sweep_seeds(
        seeds,
        time_budget_ms=args.time_budget_ms,
        candidate_limit=args.candidate_limit,
        max_search_nodes=args.max_search_nodes,
        options=GenerationOptions(candidate_cache=True),
    )

    print("\n".join(build_report(baseline, label="baseline")))
    print()
    print(
        "\n".join(
            build_comparison_report(
                baseline,
                cached,
                baseline_label="baseline",
                candidate_label="candidate_cache",
            ),
        ),
    )


if __name__ == "__main__":
    main()
