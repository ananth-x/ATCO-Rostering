from __future__ import annotations

import random
from pathlib import Path

from .models import Controller, Scenario, build_slots, normalize_code
from .workbook import extract_controllers


DEFAULT_DEMAND = {
    "M": {"RSR": 1, "ASR": 1, "P": 2, "A": 2},
    "A": {"RSR": 1, "ASR": 1, "P": 2, "A": 2},
    "N": {"RSR": 2, "ASR": 1, "P": 2, "A": 2},
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
    demand = demand_by_shift_role or DEFAULT_DEMAND
    role_names = tuple(sorted({normalize_code(role) for counts in demand.values() for role in counts}))
    slots = build_slots(days, demand)
    return Scenario(
        controllers=tuple(controllers),
        slots=slots,
        role_names=role_names,
        max_controllers=max(max_controllers or 0, len(controllers)),
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
