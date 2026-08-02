from __future__ import annotations

import csv
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from .models import Assignment, Scenario
from .validation import ValidationReport


XML_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


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
    rows = roster_matrix_rows(scenario, assignments)
    fieldnames = list(rows[0].keys()) if rows else ["controller_id", "controller_name", "qualifications"]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_roster_matrix_xlsx(path: str | Path, scenario: Scenario, assignments: list[Assignment]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = roster_matrix_rows(scenario, assignments)
    headers = list(rows[0].keys()) if rows else ["controller_id", "controller_name", "qualifications"]
    table = [headers] + [[row.get(header, "") for header in headers] for row in rows]

    with ZipFile(path, "w", ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml", _content_types_xml())
        workbook.writestr("_rels/.rels", _root_rels_xml())
        workbook.writestr("xl/workbook.xml", _workbook_xml())
        workbook.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml())
        workbook.writestr("xl/worksheets/sheet1.xml", _worksheet_xml(table))


def roster_matrix_rows(scenario: Scenario, assignments: list[Assignment]) -> list[dict[str, str]]:
    days = sorted({slot.day for slot in scenario.slots})
    assigned_shift_by_controller_day = {
        (assignment.controller_id, assignment.day): assignment.shift
        for assignment in assignments
        if assignment.controller_id is not None
    }

    rows: list[dict[str, str]] = []
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
        rows.append(row)
    return rows


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


def _content_types_xml() -> bytes:
    root = ET.Element(
        "Types",
        xmlns="http://schemas.openxmlformats.org/package/2006/content-types",
    )
    ET.SubElement(root, "Default", Extension="rels", ContentType="application/vnd.openxmlformats-package.relationships+xml")
    ET.SubElement(root, "Default", Extension="xml", ContentType="application/xml")
    ET.SubElement(
        root,
        "Override",
        PartName="/xl/workbook.xml",
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
    )
    ET.SubElement(
        root,
        "Override",
        PartName="/xl/worksheets/sheet1.xml",
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
    )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _root_rels_xml() -> bytes:
    root = ET.Element(
        "Relationships",
        xmlns="http://schemas.openxmlformats.org/package/2006/relationships",
    )
    ET.SubElement(
        root,
        "Relationship",
        Id="rId1",
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
        Target="xl/workbook.xml",
    )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _workbook_xml() -> bytes:
    ET.register_namespace("", XML_NS)
    ET.register_namespace("r", REL_NS)
    root = ET.Element(f"{{{XML_NS}}}workbook")
    sheets = ET.SubElement(root, f"{{{XML_NS}}}sheets")
    ET.SubElement(
        sheets,
        f"{{{XML_NS}}}sheet",
        name="Roster Matrix",
        sheetId="1",
        attrib={f"{{{REL_NS}}}id": "rId1"},
    )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _workbook_rels_xml() -> bytes:
    root = ET.Element(
        "Relationships",
        xmlns="http://schemas.openxmlformats.org/package/2006/relationships",
    )
    ET.SubElement(
        root,
        "Relationship",
        Id="rId1",
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
        Target="worksheets/sheet1.xml",
    )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _worksheet_xml(table: list[list[str]]) -> bytes:
    ET.register_namespace("", XML_NS)
    root = ET.Element(f"{{{XML_NS}}}worksheet")
    sheet_data = ET.SubElement(root, f"{{{XML_NS}}}sheetData")
    for row_idx, row_values in enumerate(table, start=1):
        row = ET.SubElement(sheet_data, f"{{{XML_NS}}}row", r=str(row_idx))
        for col_idx, value in enumerate(row_values, start=1):
            cell_ref = f"{_column_name(col_idx)}{row_idx}"
            cell = ET.SubElement(row, f"{{{XML_NS}}}c", r=cell_ref, t="inlineStr")
            inline = ET.SubElement(cell, f"{{{XML_NS}}}is")
            text = ET.SubElement(inline, f"{{{XML_NS}}}t")
            text.text = str(value)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name
