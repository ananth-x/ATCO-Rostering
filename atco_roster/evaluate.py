from __future__ import annotations

import csv
import json
from pathlib import Path

from .greedy import generate_greedy_roster
from .metrics import summarize_report
from .rl_env import ATCRosteringEnv
from .scenarios import scenario_from_workbook
from .validation import validate_assignments


def evaluate_greedy(
    workbook_path: str,
    days: int,
    sick_rates: list[float],
    seeds: list[int],
    output_dir: str | Path,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sick_rate in sick_rates:
        for seed in seeds:
            scenario = scenario_from_workbook(
                workbook_path,
                days=days,
                sick_rate=sick_rate,
                random_seed=seed,
            )
            env = ATCRosteringEnv(scenario)
            assignments = generate_greedy_roster(env)
            report = validate_assignments(scenario, assignments)
            rows.append(
                {
                    "method": "greedy",
                    "days": days,
                    "sick_rate": sick_rate,
                    "seed": seed,
                    **summarize_report(report),
                }
            )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "greedy_metrics.csv", rows)
    (output_dir / "greedy_metrics.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return rows


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
