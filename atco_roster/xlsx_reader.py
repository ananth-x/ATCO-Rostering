from __future__ import annotations

from datetime import date, datetime, timedelta
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile


MAIN_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"pr": "http://schemas.openxmlformats.org/package/2006/relationships"}
REL_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def col_to_num(col: str) -> int:
    value = 0
    for char in col:
        value = value * 26 + ord(char) - 64
    return value


def split_cell_ref(ref: str) -> tuple[int, int]:
    match = re.match(r"([A-Z]+)(\d+)", ref)
    if not match:
        raise ValueError(f"Invalid cell reference: {ref}")
    return int(match.group(2)), col_to_num(match.group(1))


def excel_serial_to_date(value: object) -> date | None:
    try:
        serial = float(str(value))
    except (TypeError, ValueError):
        return None
    if not 40000 <= serial <= 50000:
        return None
    return (datetime(1899, 12, 30) + timedelta(days=serial)).date()


class XlsxReader:
    """Small read-only XLSX value reader for cached workbook values."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.archive = ZipFile(self.path)
        self.shared_strings = self._load_shared_strings()
        self.sheets = self._load_sheet_targets()

    def sheet_values(self, sheet_name: str) -> dict[tuple[int, int], Any]:
        target = self.sheets[sheet_name]
        root = ET.fromstring(self.archive.read(target))
        values: dict[tuple[int, int], Any] = {}
        for cell in root.findall(".//a:c", MAIN_NS):
            ref = cell.attrib.get("r")
            if not ref:
                continue
            value = self._cell_value(cell)
            if value not in (None, ""):
                values[split_cell_ref(ref)] = value
        return values

    def close(self) -> None:
        self.archive.close()

    def _load_shared_strings(self) -> list[str]:
        if "xl/sharedStrings.xml" not in self.archive.namelist():
            return []
        root = ET.fromstring(self.archive.read("xl/sharedStrings.xml"))
        strings: list[str] = []
        for item in root.findall("a:si", MAIN_NS):
            strings.append("".join(t.text or "" for t in item.findall(".//a:t", MAIN_NS)))
        return strings

    def _load_sheet_targets(self) -> dict[str, str]:
        workbook = ET.fromstring(self.archive.read("xl/workbook.xml"))
        rels = ET.fromstring(self.archive.read("xl/_rels/workbook.xml.rels"))
        rel_targets = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall("pr:Relationship", REL_NS)
        }

        sheets: dict[str, str] = {}
        for sheet in workbook.findall("a:sheets/a:sheet", MAIN_NS):
            target = rel_targets[sheet.attrib[REL_ID]]
            sheets[sheet.attrib["name"]] = target if target.startswith("xl/") else f"xl/{target}"
        return sheets

    def _cell_value(self, cell: ET.Element) -> Any:
        value = cell.find("a:v", MAIN_NS)
        inline = cell.find("a:is", MAIN_NS)
        if value is not None and value.text is not None:
            if cell.attrib.get("t") == "s":
                index = int(value.text)
                return self.shared_strings[index] if index < len(self.shared_strings) else value.text
            return value.text
        if inline is not None:
            return "".join(t.text or "" for t in inline.findall(".//a:t", MAIN_NS))
        return None
