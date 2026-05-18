from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from statistics import mean, median
from typing import Iterable

from .app import GENERATOR
from .generator import GenerationOptions


@dataclass(frozen=True, slots=True)
class SweepRecord:
    seed: int
    status: str
    elapsed_ms: int
    answer_count: int
    template_id: str | None
    message: str | None
    search_nodes: int


def sweep_seeds(
    seeds: Iterable[int],
    *,
    time_budget_ms: int,
    candidate_limit: int,
    max_search_nodes: int,
    options: GenerationOptions | None = None,
    generator=GENERATOR,
) -> list[SweepRecord]:
    records: list[SweepRecord] = []
    for seed in seeds:
        outcome = generator.generate(
            seed=seed,
            time_budget_ms=time_budget_ms,
            candidate_limit=candidate_limit,
            max_search_nodes=max_search_nodes,
            options=options,
        )
        records.append(
            SweepRecord(
                seed=seed,
                status=outcome.status,
                elapsed_ms=outcome.stats.elapsed_ms,
                answer_count=len(outcome.answers),
                template_id=outcome.template.id if outcome.template else None,
                message=outcome.message,
                search_nodes=outcome.stats.search_nodes,
            ),
        )
    return records


def summarize(records: list[SweepRecord]) -> dict[str, object]:
    successes = [record for record in records if record.status == "ok"]
    timeouts = [record for record in records if record.status == "timeout"]
    failures = [record for record in records if record.status not in {"ok", "timeout"}]
    elapsed_success = [record.elapsed_ms for record in successes]
    nodes_success = [record.search_nodes for record in successes]

    template_success_counts: dict[str, int] = {}
    for record in successes:
        if record.template_id is None:
            continue
        template_success_counts[record.template_id] = template_success_counts.get(record.template_id, 0) + 1
    top_templates = sorted(template_success_counts.items(), key=lambda item: (-item[1], item[0]))[:10]

    return {
        "seeds_run": len(records),
        "successes": len(successes),
        "timeouts": len(timeouts),
        "other_failures": len(failures),
        "success_rate": (len(successes) / len(records)) if records else 0.0,
        "timeout_rate": (len(timeouts) / len(records)) if records else 0.0,
        "average_success_elapsed_ms": mean(elapsed_success) if elapsed_success else None,
        "median_success_elapsed_ms": median(elapsed_success) if elapsed_success else None,
        "average_success_search_nodes": mean(nodes_success) if nodes_success else None,
        "best_seed": min(successes, key=lambda record: record.elapsed_ms).seed if successes else None,
        "worst_seed": max(successes, key=lambda record: record.elapsed_ms).seed if successes else None,
        "timeout_seeds": [record.seed for record in timeouts[:25]],
        "failure_seeds": [record.seed for record in failures[:25]],
        "unique_templates_used": len(template_success_counts),
        "top_templates": [
            {"template_id": template_id, "successes": count}
            for template_id, count in top_templates
        ],
    }


def seed_series(start_seed: int, count: int, step: int) -> list[int]:
    return [start_seed + (index * step) for index in range(count)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sweep many crossword seeds and measure timeout rate.")
    parser.add_argument("--start-seed", type=int, default=1, help="First seed to try.")
    parser.add_argument("--count", type=int, default=100, help="How many sequential seeds to try.")
    parser.add_argument("--step", type=int, default=1, help="Step between seeds.")
    parser.add_argument("--time-budget-ms", type=int, default=1000, help="Per-seed time budget.")
    parser.add_argument("--candidate-limit", type=int, default=64, help="Per-slot candidate cap.")
    parser.add_argument("--max-search-nodes", type=int, default=20_000, help="Per-seed search node limit.")
    parser.add_argument("--candidate-cache", action="store_true", help="Enable the candidate lookup cache.")
    parser.add_argument("--slot-impact-tiebreak", action="store_true", help="Enable the slot-impact tie-break heuristic.")
    parser.add_argument("--template-scoring", action="store_true", help="Enable template geometry scoring.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seeds = seed_series(args.start_seed, args.count, args.step)
    options = GenerationOptions(
        candidate_cache=args.candidate_cache,
        slot_impact_tiebreak=args.slot_impact_tiebreak,
        template_scoring=args.template_scoring,
    )
    records = sweep_seeds(
        seeds,
        time_budget_ms=args.time_budget_ms,
        candidate_limit=args.candidate_limit,
        max_search_nodes=args.max_search_nodes,
        options=options,
    )
    summary = summarize(records)

    if args.json:
        print(json.dumps({"summary": summary, "records": [asdict(record) for record in records]}, indent=2))
        return

    print(f"Seeds run: {summary['seeds_run']}")
    print(f"Successes: {summary['successes']} ({summary['success_rate']:.1%})")
    print(f"Timeouts: {summary['timeouts']} ({summary['timeout_rate']:.1%})")
    print(f"Other failures: {summary['other_failures']}")
    if summary["average_success_elapsed_ms"] is not None:
        print(f"Average successful elapsed ms: {summary['average_success_elapsed_ms']:.1f}")
    if summary["median_success_elapsed_ms"] is not None:
        print(f"Median successful elapsed ms: {summary['median_success_elapsed_ms']:.1f}")
    if summary["average_success_search_nodes"] is not None:
        print(f"Average successful search nodes: {summary['average_success_search_nodes']:.1f}")
    if summary["best_seed"] is not None:
        print(f"Fastest success seed: {summary['best_seed']}")
    if summary["worst_seed"] is not None:
        print(f"Slowest success seed: {summary['worst_seed']}")
    print(f"Unique templates used: {summary['unique_templates_used']}")
    if summary["top_templates"]:
        print("Top successful templates:")
        for item in summary["top_templates"]:
            print(f"  {item['template_id']}: {item['successes']} successes")
    if summary["timeout_seeds"]:
        print("Timeout seeds (first 25): " + ", ".join(str(seed) for seed in summary["timeout_seeds"]))
    if summary["failure_seeds"]:
        print("Other failure seeds (first 25): " + ", ".join(str(seed) for seed in summary["failure_seeds"]))


if __name__ == "__main__":
    main()
