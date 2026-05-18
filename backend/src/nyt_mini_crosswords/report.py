from __future__ import annotations

import argparse
from typing import Iterable

from .generator import GenerationOptions
from .sweep import SweepRecord, align_records, seed_series, summarize, summarize_comparison, sweep_seeds


def build_report(records: list[SweepRecord], *, label: str | None = None) -> list[str]:
    summary = summarize(records)
    lines: list[str] = []
    if label:
        lines.append(f"Report: {label}")
    lines.append(f"Seeds run: {summary['seeds_run']}")
    lines.append(f"Successes: {summary['successes']} ({summary['success_rate']:.1%})")
    lines.append(f"Timeouts: {summary['timeouts']} ({summary['timeout_rate']:.1%})")
    lines.append(f"Other failures: {summary['other_failures']}")
    if summary["average_success_elapsed_ms"] is not None:
        lines.append(f"Average success elapsed ms: {summary['average_success_elapsed_ms']:.1f}")
    if summary["median_success_elapsed_ms"] is not None:
        lines.append(f"Median success elapsed ms: {summary['median_success_elapsed_ms']:.1f}")
    if summary["average_success_search_nodes"] is not None:
        lines.append(f"Average success search nodes: {summary['average_success_search_nodes']:.1f}")
    if summary["best_seed"] is not None:
        lines.append(f"Fastest success seed: {summary['best_seed']}")
    if summary["worst_seed"] is not None:
        lines.append(f"Slowest success seed: {summary['worst_seed']}")
    lines.append(f"Unique templates used: {summary['unique_templates_used']}")
    if summary["top_templates"]:
        lines.append("Top successful templates:")
        for item in summary["top_templates"]:
            lines.append(f"  {item['template_id']}: {item['successes']} successes")
    if summary["timeout_seeds"]:
        lines.append("Timeout seeds (first 25): " + ", ".join(str(seed) for seed in summary["timeout_seeds"]))
    if summary["failure_seeds"]:
        lines.append("Other failure seeds (first 25): " + ", ".join(str(seed) for seed in summary["failure_seeds"]))
    return lines


def build_comparison_report(
    baseline: list[SweepRecord],
    candidate: list[SweepRecord],
    *,
    baseline_label: str = "baseline",
    candidate_label: str = "candidate",
) -> list[str]:
    pairs = align_records(baseline, candidate)
    summary = summarize_comparison(pairs)
    lines: list[str] = []
    lines.append(f"Comparison: {candidate_label} vs {baseline_label}")
    lines.append(f"Seeds compared: {summary['seeds_compared']}")
    lines.append(f"{baseline_label} successes: {summary['baseline_successes']} ({(summary['baseline_successes'] / summary['seeds_compared'] if summary['seeds_compared'] else 0.0):.1%})")
    lines.append(f"{candidate_label} successes: {summary['candidate_successes']} ({(summary['candidate_successes'] / summary['seeds_compared'] if summary['seeds_compared'] else 0.0):.1%})")
    lines.append(f"Success delta: {summary['success_delta']:+d}")
    lines.append(f"Improved seeds: {summary['improved']}")
    lines.append(f"Regressed seeds: {summary['regressed']}")
    lines.append(f"Shared successes: {summary['shared_successes']}")
    lines.append(f"Shared timeouts: {summary['shared_timeouts']}")
    if summary["elapsed_delta_mean_ms"] is not None:
        lines.append(f"Mean elapsed delta on shared successes: {summary['elapsed_delta_mean_ms']:+.1f} ms")
    if summary["elapsed_delta_median_ms"] is not None:
        lines.append(f"Median elapsed delta on shared successes: {summary['elapsed_delta_median_ms']:+.1f} ms")
    if summary["search_node_delta_mean"] is not None:
        lines.append(f"Mean search-node delta on shared successes: {summary['search_node_delta_mean']:+.1f}")
    if summary["search_node_delta_median"] is not None:
        lines.append(f"Median search-node delta on shared successes: {summary['search_node_delta_median']:+.1f}")
    lines.append(f"Exact match rate on shared successes: {summary['exact_match_rate']:.1%}")
    if summary["candidate_only_seeds"]:
        lines.append(f"Seeds improved by {candidate_label} (first 25): " + ", ".join(str(seed) for seed in summary["candidate_only_seeds"]))
    if summary["baseline_only_seeds"]:
        lines.append(f"Seeds regressed from {baseline_label} (first 25): " + ", ".join(str(seed) for seed in summary["baseline_only_seeds"]))
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a human-readable crossword generation report.")
    parser.add_argument("--label", default=None, help="Optional label for the configuration being measured.")
    parser.add_argument("--start-seed", type=int, default=1, help="First seed to try.")
    parser.add_argument("--count", type=int, default=100, help="How many sequential seeds to try.")
    parser.add_argument("--step", type=int, default=1, help="Step between seeds.")
    parser.add_argument("--time-budget-ms", type=int, default=1000, help="Per-seed time budget.")
    parser.add_argument("--candidate-limit", type=int, default=64, help="Per-slot candidate cap.")
    parser.add_argument("--max-search-nodes", type=int, default=20_000, help="Per-seed search node limit.")
    parser.add_argument("--candidate-cache", action="store_true", help="Enable the candidate lookup cache.")
    parser.add_argument("--slot-impact-tiebreak", action="store_true", help="Enable the slot-impact tie-break heuristic.")
    parser.add_argument("--template-scoring", action="store_true", help="Enable template geometry scoring.")
    return parser.parse_args()


def run_report(
    seeds: Iterable[int],
    *,
    time_budget_ms: int,
    candidate_limit: int,
    max_search_nodes: int,
    options: GenerationOptions | None = None,
    label: str | None = None,
) -> list[str]:
    records = sweep_seeds(
        seeds,
        time_budget_ms=time_budget_ms,
        candidate_limit=candidate_limit,
        max_search_nodes=max_search_nodes,
        options=options,
    )
    return build_report(records, label=label)


def main() -> None:
    args = parse_args()
    seeds = seed_series(args.start_seed, args.count, args.step)
    options = GenerationOptions(
        candidate_cache=args.candidate_cache,
        slot_impact_tiebreak=args.slot_impact_tiebreak,
        template_scoring=args.template_scoring,
    )
    for line in run_report(
        seeds,
        time_budget_ms=args.time_budget_ms,
        candidate_limit=args.candidate_limit,
        max_search_nodes=args.max_search_nodes,
        options=options,
        label=args.label,
    ):
        print(line)


if __name__ == "__main__":
    main()
