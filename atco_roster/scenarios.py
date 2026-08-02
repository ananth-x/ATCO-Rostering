from __future__ import annotations

import json
import random
from pathlib import Path

from .models import Controller, Scenario, build_slots, normalize_code
from .workbook import extract_controllers


DEFAULT_DEMAND = {
    "M": {"RSR": 1, "ASR": 1, "P": 2, "A": 2},
    "A": {"RSR": 1, "ASR": 1, "P": 2, "A": 2},
    "N": {"RSR": 2, "ASR": 1, "P": 2, "A": 2},
}

AAI_SAMPLE_DEMAND = {
    "M": {"RSR": 4, "ASR": 2, "ADC": 6, "P": 6, "A": 6},
    "A": {"RSR": 4, "ASR": 2, "ADC": 6, "P": 6, "A": 6},
    "N": {"RSR": 4, "ASR": 2, "ADC": 6, "P": 6, "A": 6},
}

DEMAND_PROFILES = {
    "conservative": DEFAULT_DEMAND,
    "aai_sample": AAI_SAMPLE_DEMAND,
}


def scenario_from_workbook(
    workbook_path: str | Path,
    days: int,
    demand_by_shift_role: dict[str, dict[str, int]] | None = None,
    max_controllers: int | None = None,
    sick_rate: float = 0.0,
    random_seed: int = 42,
) -> Scenario:
    controllers = list(extract_controllers(workbook_path))
    if sick_rate:
        controllers = _add_synthetic_absences(controllers, days, sick_rate, random_seed)
    demand = normalize_demand(demand_by_shift_role or DEFAULT_DEMAND)
    role_names = tuple(sorted({normalize_code(role) for counts in demand.values() for role in counts}))
    slots = build_slots(days, demand)
    return Scenario(
        controllers=tuple(controllers),
        slots=slots,
        role_names=role_names,
        max_controllers=max(max_controllers or 0, len(controllers)),
        night_recovery_days=2,
    )


def scenario_from_config(config_path: str | Path) -> Scenario:
    path = Path(config_path)
    config = json.loads(path.read_text(encoding="utf-8"))
    days = int(config["days"])
    demand = _demand_from_config(config)
    controllers = _controllers_from_config(config, path.parent)
    role_names = tuple(sorted({normalize_code(role) for counts in demand.values() for role in counts}))
    constraints = config.get("constraints", {})
    slots = build_slots(days, demand)
    max_controllers = int(config.get("max_controllers") or len(controllers))
    return Scenario(
        controllers=tuple(controllers),
        slots=slots,
        role_names=role_names,
        max_controllers=max(max_controllers, len(controllers)),
        min_rest_hours=float(constraints.get("min_rest_hours", 12.0)),
        max_consecutive_days=int(constraints.get("max_consecutive_days", 4)),
        currency_threshold_days=int(constraints.get("currency_threshold_days", 50)),
        night_recovery_days=int(constraints.get("night_recovery_days", 2)),
    )


def demand_profile(name: str) -> dict[str, dict[str, int]]:
    try:
        return DEMAND_PROFILES[name]
    except KeyError as exc:
        allowed = ", ".join(sorted(DEMAND_PROFILES))
        raise ValueError(f"Unknown demand profile {name!r}. Allowed values: {allowed}") from exc


def normalize_demand(demand: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    normalized: dict[str, dict[str, int]] = {}
    for shift, role_counts in demand.items():
        normalized_shift = normalize_code(shift)
        normalized[normalized_shift] = {
            normalize_code(role): int(count)
            for role, count in role_counts.items()
            if int(count) > 0
        }
    return normalized


def _demand_from_config(config: dict) -> dict[str, dict[str, int]]:
    if "demand" in config:
        return normalize_demand(config["demand"])
    return normalize_demand(demand_profile(config.get("demand_profile", "conservative")))


def _controllers_from_config(config: dict, base_dir: Path) -> list[Controller]:
    if "controllers" in config:
        return [_controller_from_dict(item) for item in config["controllers"]]

    if "workbook" not in config:
        raise ValueError("Scenario config must provide either 'controllers' or 'workbook'")

    workbook_path = Path(config["workbook"])
    if not workbook_path.is_absolute():
        workbook_path = base_dir / workbook_path
    controllers = list(extract_controllers(workbook_path))
    unavailable_by_controller = {
        str(controller_id): set(days)
        for controller_id, days in config.get("unavailable_by_controller", {}).items()
    }
    if not unavailable_by_controller:
        return controllers

    updated: list[Controller] = []
    for controller in controllers:
        unavailable = unavailable_by_controller.get(controller.controller_id, set())
        updated.append(
            Controller(
                controller.controller_id,
                controller.name,
                controller.qualifications,
                frozenset(int(day) for day in unavailable),
                controller.days_since_role,
            )
        )
    return updated


def _controller_from_dict(item: dict) -> Controller:
    unavailable = frozenset(int(day) for day in item.get("unavailable_days", []))
    days_since_role = {
        normalize_code(role): int(days)
        for role, days in item.get("days_since_role", {}).items()
    }
    if "qualifications" in item:
        return Controller(
            str(item["id"]),
            str(item["name"]),
            tuple(normalize_code(role) for role in item["qualifications"]),
            unavailable,
            days_since_role,
        )
    controller = Controller.from_rating(
        str(item["id"]),
        str(item["name"]),
        str(item["rating"]),
        unavailable,
    )
    return Controller(
        controller.controller_id,
        controller.name,
        controller.qualifications,
        controller.unavailable_days,
        days_since_role,
    )


def _add_synthetic_absences(
    controllers: list[Controller],
    days: int,
    sick_rate: float,
    random_seed: int,
) -> list[Controller]:
    rng = random.Random(random_seed)
    updated: list[Controller] = []
    for controller in controllers:
        unavailable = set(controller.unavailable_days)
        if rng.random() < sick_rate:
            start = rng.randrange(max(1, days))
            length = rng.randint(1, min(3, days - start))
            unavailable.update(range(start, start + length))
        updated.append(
            Controller(
                controller.controller_id,
                controller.name,
                controller.qualifications,
                frozenset(unavailable),
                controller.days_since_role,
            )
        )
    return updated
