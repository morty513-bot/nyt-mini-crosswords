from __future__ import annotations

import argparse

from nyt_mini_crosswords.generator import GenerationOptions
from nyt_mini_crosswords.report import build_comparison_report, build_report
from nyt_mini_crosswords.sweep import seed_series, sweep_seeds


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
    records_by_label: dict[str, list] = {}
    for label, options in configs:
        records_by_label[label] = sweep_seeds(
            seeds,
            time_budget_ms=args.time_budget_ms,
            candidate_limit=args.candidate_limit,
            max_search_nodes=args.max_search_nodes,
            options=options,
        )

    baseline_label = "baseline"
    print("\n".join(build_report(records_by_label[baseline_label], label=baseline_label)))
    for label, _ in configs[1:]:
        print()
        print("\n".join(
            build_comparison_report(
                records_by_label[baseline_label],
                records_by_label[label],
                baseline_label=baseline_label,
                candidate_label=label,
            ),
        ))


if __name__ == "__main__":
    main()
