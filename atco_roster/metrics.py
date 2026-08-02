from __future__ import annotations

from statistics import mean, pstdev

from .validation import ValidationReport


def summarize_report(report: ValidationReport) -> dict[str, float | int | bool]:
    hours = list(report.hours_by_controller.values())
    coverage = report.filled_slots / report.total_slots if report.total_slots else 0.0
    return {
        "total_slots": report.total_slots,
        "filled_slots": report.filled_slots,
        "empty_slots": report.empty_slots,
        "coverage": round(coverage, 6),
        "hard_violations": len(report.hard_violations),
        "is_valid": report.is_valid,
        "mean_hours": round(mean(hours), 6) if hours else 0.0,
        "std_hours": round(pstdev(hours), 6) if len(hours) > 1 else 0.0,
        "max_hours": round(max(hours), 6) if hours else 0.0,
        "min_hours": round(min(hours), 6) if hours else 0.0,
    }
