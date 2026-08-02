from __future__ import annotations

import argparse
import json
from pathlib import Path

from .export import export_assignments_csv, export_report_json
from .greedy import generate_greedy_roster
from .rl_env import ATCRosteringEnv
from .scenarios import scenario_from_workbook
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
    generate.add_argument("--output-dir", default="outputs/atco_roster")

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
        scenario = scenario_from_workbook(args.workbook, args.days, sick_rate=args.sick_rate)
        env = ATCRosteringEnv(scenario)
        assignments = generate_greedy_roster(env)
        report = validate_assignments(scenario, assignments)
        output_dir = Path(args.output_dir)
        export_assignments_csv(output_dir / "generated_roster.csv", scenario, assignments)
        export_report_json(output_dir / "validation_report.json", report)
        print(f"Filled {report.filled_slots}/{report.total_slots} slots")
        print(f"Hard violations: {len(report.hard_violations)}")
        print(f"Wrote {output_dir / 'generated_roster.csv'}")
        print(f"Wrote {output_dir / 'validation_report.json'}")


if __name__ == "__main__":
    main()
