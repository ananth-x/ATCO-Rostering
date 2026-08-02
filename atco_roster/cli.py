from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluate import evaluate_greedy
from .export import export_assignments_csv, export_report_json, export_roster_matrix_csv
from .greedy import generate_greedy_roster
from .rl_train import train_maskable_ppo
from .rl_env import ATCRosteringEnv
from .scenarios import demand_profile, scenario_from_workbook
from .validation import validate_assignments
from .workbook import summarize_duty_sheet


def main() -> None:
    parser = argparse.ArgumentParser(description="ATCO rostering tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze-workbook")
    analyze.add_argument("workbook")
    analyze.add_argument("--sheet", action="append", default=[])
    analyze.add_argument("--output", default="outputs/atco_roster/workbook_summary.json")

    generate = subparsers.add_parser("generate-greedy")
    generate.add_argument("workbook")
    generate.add_argument("--days", type=int, default=10)
    generate.add_argument("--sick-rate", type=float, default=0.0)
    generate.add_argument("--demand-profile", default="conservative")
    generate.add_argument("--demand-json")
    generate.add_argument("--output-dir", default="outputs/atco_roster")

    train = subparsers.add_parser("train-rl")
    train.add_argument("workbook")
    train.add_argument("--days", type=int, default=10)
    train.add_argument("--timesteps", type=int, default=60000)
    train.add_argument("--sick-rate", type=float, default=0.0)
    train.add_argument("--max-controllers", type=int)
    train.add_argument("--demand-profile", default="conservative")
    train.add_argument("--demand-json")
    train.add_argument("--n-steps", type=int, default=1024)
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--output-dir", default="outputs/atco_roster/rl_run")

    evaluate = subparsers.add_parser("evaluate-greedy")
    evaluate.add_argument("workbook")
    evaluate.add_argument("--days", type=int, default=10)
    evaluate.add_argument("--sick-rate", action="append", type=float, default=[])
    evaluate.add_argument("--seeds", type=int, default=10)
    evaluate.add_argument("--demand-profile", default="conservative")
    evaluate.add_argument("--demand-json")
    evaluate.add_argument("--output-dir", default="outputs/atco_roster/experiments")

    args = parser.parse_args()
    if args.command == "analyze-workbook":
        sheets = args.sheet or ["JAN 24 DUTIES", "JULY 24 DUTIES", "OCTOBER 24 DUTIES"]
        summaries = [summarize_duty_sheet(args.workbook, sheet) for sheet in sheets]
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
        print(f"Wrote {output}")
        return

    if args.command == "generate-greedy":
        demand = _load_demand(args.demand_profile, args.demand_json)
        scenario = scenario_from_workbook(
            args.workbook,
            args.days,
            demand_by_shift_role=demand,
            sick_rate=args.sick_rate,
        )
        env = ATCRosteringEnv(scenario)
        assignments = generate_greedy_roster(env)
        report = validate_assignments(scenario, assignments)
        output_dir = Path(args.output_dir)
        export_assignments_csv(output_dir / "generated_roster.csv", scenario, assignments)
        export_roster_matrix_csv(output_dir / "generated_roster_matrix.csv", scenario, assignments)
        export_report_json(output_dir / "validation_report.json", report)
        print(f"Filled {report.filled_slots}/{report.total_slots} slots")
        print(f"Hard violations: {len(report.hard_violations)}")
        print(f"Wrote {output_dir / 'generated_roster.csv'}")
        print(f"Wrote {output_dir / 'generated_roster_matrix.csv'}")
        print(f"Wrote {output_dir / 'validation_report.json'}")
        return

    if args.command == "train-rl":
        demand = _load_demand(args.demand_profile, args.demand_json)
        train_maskable_ppo(
            args.workbook,
            days=args.days,
            total_timesteps=args.timesteps,
            output_dir=args.output_dir,
            sick_rate=args.sick_rate,
            max_controllers=args.max_controllers,
            demand_by_shift_role=demand,
            n_steps=args.n_steps,
            seed=args.seed,
        )
        print(f"Wrote RL artifacts to {args.output_dir}")
        return

    if args.command == "evaluate-greedy":
        demand = _load_demand(args.demand_profile, args.demand_json)
        sick_rates = args.sick_rate or [0.0, 0.1, 0.2, 0.3]
        rows = evaluate_greedy(
            args.workbook,
            days=args.days,
            demand_by_shift_role=demand,
            sick_rates=sick_rates,
            seeds=list(range(args.seeds)),
            output_dir=args.output_dir,
        )
        valid_runs = sum(1 for row in rows if row["is_valid"])
        avg_coverage = sum(float(row["coverage"]) for row in rows) / max(1, len(rows))
        print(f"Runs: {len(rows)}")
        print(f"Valid runs: {valid_runs}/{len(rows)}")
        print(f"Average coverage: {avg_coverage:.3f}")
        print(f"Wrote metrics to {args.output_dir}")


def _load_demand(profile: str, demand_json: str | None) -> dict[str, dict[str, int]]:
    if demand_json:
        path = Path(demand_json)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return json.loads(demand_json)
    return demand_profile(profile)


if __name__ == "__main__":
    main()
