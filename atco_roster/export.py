from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import Assignment, Scenario
from .validation import ValidationReport


def export_assignments_csv(path: str | Path, scenario: Scenario, assignments: list[Assignment]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    controllers = {controller.controller_id: controller for controller in scenario.controllers}
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["day", "shift", "role", "slot_number", "controller_id", "controller_name"],
        )
        writer.writeheader()
        for assignment in assignments:
            controller = controllers.get(assignment.controller_id or "")
            writer.writerow(
                {
                    "day": assignment.day,
                    "shift": assignment.shift,
                    "role": assignment.role,
                    "slot_number": assignment.slot_number,
                    "controller_id": assignment.controller_id or "EMPTY",
                    "controller_name": controller.name if controller else "EMPTY",
                }
            )


def export_report_json(path: str | Path, report: ValidationReport) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "total_slots": report.total_slots,
        "filled_slots": report.filled_slots,
        "empty_slots": report.empty_slots,
        "is_valid": report.is_valid,
        "hard_violations": list(report.hard_violations),
        "hours_by_controller": report.hours_by_controller,
        "coverage_by_shift_role": report.coverage_by_shift_role,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
