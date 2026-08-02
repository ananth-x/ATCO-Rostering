from __future__ import annotations

import csv
import json
from pathlib import Path

from .greedy import generate_greedy_roster
from .metrics import summarize_report
from .rl_env import ATCRosteringEnv
from .rl_train import train_maskable_ppo_for_scenario
from .scenarios import scenario_from_config, scenario_from_workbook
from .validation import validate_assignments


def evaluate_greedy(
    workbook_path: str,
    days: int,
    demand_by_shift_role: dict[str, dict[str, int]],
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
                demand_by_shift_role=demand_by_shift_role,
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


def evaluate_config(
    config_path: str | Path,
    seeds: list[int],
    output_dir: str | Path,
    rl_timesteps: int,
    n_steps: int = 1024,
    include_rl: bool = True,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    output_dir = Path(output_dir)
    for seed in seeds:
        scenario = scenario_from_config(config_path)
        env = ATCRosteringEnv(scenario)
        assignments = generate_greedy_roster(env)
        greedy_report = validate_assignments(scenario, assignments)
        rows.append(
            {
                "method": "greedy",
                "config": str(config_path),
                "seed": seed,
                "timesteps": 0,
                **summarize_report(greedy_report),
            }
        )

        if include_rl and rl_timesteps > 0:
            scenario = scenario_from_config(config_path)
            rl_report = train_maskable_ppo_for_scenario(
                scenario,
                total_timesteps=rl_timesteps,
                output_dir=output_dir / f"rl_seed_{seed}",
                n_steps=n_steps,
                seed=seed,
            )
            rows.append(
                {
                    "method": "rl_maskable_ppo",
                    "config": str(config_path),
                    "seed": seed,
                    "timesteps": rl_timesteps,
                    **summarize_report(rl_report),
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "config_metrics.csv", rows)
    (output_dir / "config_metrics.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return rows


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
