from __future__ import annotations

from pathlib import Path

from .export import (
    export_assignments_csv,
    export_report_json,
    export_roster_matrix_csv,
    export_roster_matrix_xlsx,
)
from .rl_env import ATCRosteringEnv
from .models import Scenario
from .scenarios import scenario_from_workbook
from .validation import ValidationReport, validate_assignments


def train_maskable_ppo(
    workbook_path: str,
    days: int,
    total_timesteps: int,
    output_dir: str | Path,
    sick_rate: float = 0.0,
    max_controllers: int | None = None,
    demand_by_shift_role: dict[str, dict[str, int]] | None = None,
    n_steps: int = 1024,
    seed: int = 42,
    verbose: int = 0,
) -> ValidationReport:
    scenario = scenario_from_workbook(
        workbook_path,
        days=days,
        demand_by_shift_role=demand_by_shift_role,
        max_controllers=max_controllers,
        sick_rate=sick_rate,
        random_seed=seed,
    )
    return train_maskable_ppo_for_scenario(
        scenario,
        total_timesteps=total_timesteps,
        output_dir=output_dir,
        n_steps=n_steps,
        seed=seed,
        verbose=verbose,
    )


def train_maskable_ppo_for_scenario(
    scenario: Scenario,
    total_timesteps: int,
    output_dir: str | Path,
    n_steps: int = 1024,
    seed: int = 42,
    verbose: int = 0,
) -> ValidationReport:
    try:
        from sb3_contrib import MaskablePPO
        from sb3_contrib.common.wrappers import ActionMasker
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing RL dependencies. Install them with: "
            "python3 -m pip install -r requirements-atco.txt"
        ) from exc

    base_env = ATCRosteringEnv(scenario)
    env = ActionMasker(base_env, lambda wrapped_env: wrapped_env.valid_action_mask())

    model = MaskablePPO(
        "MlpPolicy",
        env,
        gamma=0.95,
        learning_rate=1e-3,
        n_steps=n_steps,
        batch_size=min(128, n_steps),
        ent_coef=0.01,
        seed=seed,
        verbose=verbose,
    )
    model.learn(total_timesteps=total_timesteps)

    obs, _ = env.reset(seed=seed)
    done = False
    while not done:
        action, _ = model.predict(obs, action_masks=env.action_masks(), deterministic=True)
        obs, _, done, _, _ = env.step(action)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save(output_dir / "maskable_ppo_atco")
    assignments = list(base_env.assignments)
    report = validate_assignments(scenario, assignments)
    export_assignments_csv(output_dir / "rl_generated_roster.csv", scenario, assignments)
    export_roster_matrix_csv(output_dir / "rl_generated_roster_matrix.csv", scenario, assignments)
    export_roster_matrix_xlsx(output_dir / "rl_generated_roster_matrix.xlsx", scenario, assignments)
    export_report_json(output_dir / "rl_validation_report.json", report)
    return report
