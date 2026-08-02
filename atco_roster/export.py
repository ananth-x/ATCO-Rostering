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


def export_roster_matrix_csv(path: str | Path, scenario: Scenario, assignments: list[Assignment]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    days = sorted({slot.day for slot in scenario.slots})
    assigned_shift_by_controller_day = {
        (assignment.controller_id, assignment.day): assignment.shift
        for assignment in assignments
        if assignment.controller_id is not None
    }

    with path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["controller_id", "controller_name", "qualifications"] + [
            f"D{day + 1:02d}" for day in days
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for controller in scenario.controllers:
            row = {
                "controller_id": controller.controller_id,
                "controller_name": controller.name,
                "qualifications": "/".join(controller.qualifications),
            }
            previous_code = ""
            for day in days:
                code = assigned_shift_by_controller_day.get((controller.controller_id, day))
                if day in controller.unavailable_days:
                    code = "L"
                elif code is None:
                    code = "NO" if previous_code == "N" else "O"
                row[f"D{day + 1:02d}"] = code
                previous_code = code
            writer.writerow(row)


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
