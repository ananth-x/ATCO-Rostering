from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from .models import Assignment, Scenario


@dataclass(frozen=True)
class ValidationReport:
    total_slots: int
    filled_slots: int
    empty_slots: int
    hard_violations: tuple[str, ...]
    hours_by_controller: dict[str, float]
    coverage_by_shift_role: dict[str, int]

    @property
    def is_valid(self) -> bool:
        return not self.hard_violations


def validate_assignments(
    scenario: Scenario,
    assignments: list[Assignment],
) -> ValidationReport:
    slot_by_key = {
        (slot.day, slot.shift, slot.role, slot.slot_number): slot for slot in scenario.slots
    }
    controllers = {controller.controller_id: controller for controller in scenario.controllers}
    by_controller: dict[str, list[Assignment]] = defaultdict(list)
    hours_by_controller: dict[str, float] = defaultdict(float)
    hard_violations: list[str] = []
    coverage: Counter[str] = Counter()

    seen_slots = set()
    for assignment in assignments:
        key = (assignment.day, assignment.shift, assignment.role, assignment.slot_number)
        slot = slot_by_key.get(key)
        if slot is None:
            hard_violations.append(f"Unknown slot assigned: {key}")
            continue
        if key in seen_slots:
            hard_violations.append(f"Duplicate slot assignment: {key}")
        seen_slots.add(key)
        coverage[f"D{assignment.day}:{assignment.shift}:{assignment.role}"] += int(
            assignment.controller_id is not None
        )
        if assignment.controller_id is None:
            continue
        controller = controllers.get(assignment.controller_id)
        if controller is None:
            hard_violations.append(f"Unknown controller: {assignment.controller_id}")
            continue
        if assignment.day in controller.unavailable_days:
            hard_violations.append(f"{controller.name} assigned while unavailable on day {assignment.day}")
        if assignment.role not in controller.qualifications:
            hard_violations.append(f"{controller.name} lacks qualification for {assignment.role}")
        by_controller[controller.controller_id].append(assignment)
        hours_by_controller[controller.controller_id] += slot.duration_hours

    missing_slots = set(slot_by_key) - seen_slots
    for key in sorted(missing_slots):
        hard_violations.append(f"Missing slot assignment: {key}")

    for controller_id, controller_assignments in by_controller.items():
        ordered = sorted(
            controller_assignments,
            key=lambda item: slot_by_key[(item.day, item.shift, item.role, item.slot_number)].start_hour,
        )
        previous_end = None
        previous_day = None
        streak = 0
        days_seen = set()
        for assignment in ordered:
            slot = slot_by_key[(assignment.day, assignment.shift, assignment.role, assignment.slot_number)]
            if assignment.day in days_seen:
                hard_violations.append(f"{controller_id} has multiple assignments on day {assignment.day}")
            days_seen.add(assignment.day)
            if previous_end is not None and slot.start_hour - previous_end < scenario.min_rest_hours:
                hard_violations.append(
                    f"{controller_id} has only {slot.start_hour - previous_end:.1f}h rest before day "
                    f"{assignment.day} {assignment.shift}"
                )
            if previous_day == assignment.day - 1:
                streak += 1
            else:
                streak = 1
            if streak > scenario.max_consecutive_days:
                hard_violations.append(
                    f"{controller_id} exceeds {scenario.max_consecutive_days} consecutive days"
                )
            previous_day = assignment.day
            previous_end = slot.end_hour

    total_slots = len(scenario.slots)
    filled_slots = sum(1 for item in assignments if item.controller_id is not None)
    return ValidationReport(
        total_slots=total_slots,
        filled_slots=filled_slots,
        empty_slots=total_slots - filled_slots,
        hard_violations=tuple(hard_violations),
        hours_by_controller=dict(sorted(hours_by_controller.items())),
        coverage_by_shift_role=dict(sorted(coverage.items())),
    )
