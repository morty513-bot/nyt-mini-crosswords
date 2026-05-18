from __future__ import annotations

import argparse

from nyt_mini_crosswords.generator import GenerationOptions
from nyt_mini_crosswords.report import run_report
from nyt_mini_crosswords.sweep import seed_series


def build_configs() -> list[tuple[str, GenerationOptions]]:
    return [
        ("baseline", GenerationOptions(candidate_cache=False, slot_impact_tiebreak=False, template_scoring=False)),
        ("candidate_cache", GenerationOptions(candidate_cache=True, slot_impact_tiebreak=False, template_scoring=False)),
        ("slot_impact_tiebreak", GenerationOptions(candidate_cache=False, slot_impact_tiebreak=True, template_scoring=False)),
        ("template_scoring", GenerationOptions(candidate_cache=False, slot_impact_tiebreak=False, template_scoring=True)),
        ("all_on", GenerationOptions(candidate_cache=True, slot_impact_tiebreak=True, template_scoring=True)),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare crossword generator optimization settings.")
    parser.add_argument("--start-seed", type=int, default=1, help="First seed to try.")
    parser.add_argument("--count", type=int, default=50, help="How many sequential seeds to try per config.")
    parser.add_argument("--step", type=int, default=1, help="Step between seeds.")
    parser.add_argument("--time-budget-ms", type=int, default=1000, help="Per-seed time budget.")
    parser.add_argument("--candidate-limit", type=int, default=64, help="Per-slot candidate cap.")
    parser.add_argument("--max-search-nodes", type=int, default=20_000, help="Per-seed search node limit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seeds = seed_series(args.start_seed, args.count, args.step)
    configs = build_configs()
    for index, (label, options) in enumerate(configs):
        for line in run_report(
            seeds,
            time_budget_ms=args.time_budget_ms,
            candidate_limit=args.candidate_limit,
            max_search_nodes=args.max_search_nodes,
            options=options,
            label=label,
        ):
            print(line)
        if index + 1 < len(configs):
            print()


if __name__ == "__main__":
    main()
