from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .models import Controller, normalize_code
from .xlsx_reader import XlsxReader, excel_serial_to_date


IGNORED_RATINGS = {"", "0", "28", "30", "36", "144", "146"}
LEAVE_CODES = {"L", "CL", "EL", "RH", "MED", "ML", "HPL"}


def extract_controllers(
    workbook_path: str | Path,
    sheet_name: str = "IMPLEMENTED ROSTER 2024",
) -> tuple[Controller, ...]:
    reader = XlsxReader(workbook_path)
    try:
        values = reader.sheet_values(sheet_name)
    finally:
        reader.close()

    header_row = _find_header_row(values)
    headers = _row_map(values, header_row)
    emp_col = _first_header(headers, "EMPLOYEE")
    name_col = _first_header(headers, "NAME OF THE OFFICER")
    rating_col = _first_header(headers, "RATINGS")

    controllers: list[Controller] = []
    for row in range(header_row + 1, _max_row(values) + 1):
        employee = values.get((row, emp_col))
        name = values.get((row, name_col))
        rating = normalize_code(values.get((row, rating_col)))
        if not employee or not name or rating in IGNORED_RATINGS:
            continue
        controllers.append(Controller.from_rating(str(employee), str(name), rating))
    return tuple(controllers)


def summarize_duty_sheet(
    workbook_path: str | Path,
    sheet_name: str,
) -> dict[str, Any]:
    reader = XlsxReader(workbook_path)
    try:
        values = reader.sheet_values(sheet_name)
    finally:
        reader.close()

    header_row = _find_header_row(values)
    headers = _row_map(values, header_row)
    emp_col = _first_header(headers, "EMPLOYEE")
    rating_col = _first_existing_header(headers, ("RATINGS", "RATINGS(R/T/A)"))
    shift_col = _first_header(headers, "SHIFT")
    date_cols = {
        col: excel_serial_to_date(label)
        for col, label in headers.items()
        if excel_serial_to_date(label)
    }

    team_counts: Counter[str] = Counter()
    rating_counts: Counter[str] = Counter()
    code_counts: Counter[str] = Counter()
    employees = 0

    for row in range(header_row + 1, _max_row(values) + 1):
        employee = values.get((row, emp_col))
        rating = normalize_code(values.get((row, rating_col)))
        if not employee or rating in IGNORED_RATINGS:
            continue
        employees += 1
        team_counts[normalize_code(values.get((row, shift_col)))] += 1
        rating_counts[rating] += 1
        for col in date_cols:
            code = normalize_code(values.get((row, col)))
            if code:
                code_counts[code] += 1

    dates = [day for day in date_cols.values() if day is not None]
    return {
        "sheet": sheet_name,
        "employees": employees,
        "start_date": min(dates).isoformat() if dates else None,
        "end_date": max(dates).isoformat() if dates else None,
        "days": len(dates),
        "teams": dict(sorted(team_counts.items())),
        "ratings": dict(sorted(rating_counts.items())),
        "codes": dict(code_counts.most_common()),
    }


def _find_header_row(values: dict[tuple[int, int], Any]) -> int:
    for (row, _), value in values.items():
        if str(value).upper().replace(" ", "").startswith("EMPLOYEENO"):
            return row
    raise ValueError("Could not find Employee No. header row")


def _row_map(values: dict[tuple[int, int], Any], row: int) -> dict[int, str]:
    return {
        col: str(value).strip()
        for (current_row, col), value in values.items()
        if current_row == row
    }


def _first_header(headers: dict[int, str], prefix: str) -> int:
    prefix = prefix.upper()
    for col, label in headers.items():
        if label.upper().startswith(prefix):
            return col
    raise ValueError(f"Missing header starting with {prefix!r}")


def _first_existing_header(headers: dict[int, str], labels: tuple[str, ...]) -> int:
    normalized = {label.upper(): col for col, label in headers.items()}
    for label in labels:
        if label in normalized:
            return normalized[label]
    return _first_header(headers, labels[0])


def _max_row(values: dict[tuple[int, int], Any]) -> int:
    return max(row for row, _ in values)
