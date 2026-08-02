import csv
from pathlib import Path
import tempfile
from zipfile import ZipFile

from atco_roster.export import export_roster_matrix_csv, export_roster_matrix_xlsx
from atco_roster.models import Assignment, Controller, Scenario, build_slots


class ExportTests:
    def test_roster_matrix_uses_shift_leave_night_off_and_off_codes(self):
        controllers = (
            Controller("1", "Night Worker", ("RSR",)),
            Controller("2", "Unavailable", ("RSR",), frozenset({1})),
        )
        scenario = Scenario(
            controllers=controllers,
            slots=build_slots(3, {"N": {"RSR": 1}}),
            role_names=("RSR",),
            max_controllers=2,
        )
        assignments = [
            Assignment(0, "N", "RSR", 1, "1"),
            Assignment(1, "N", "RSR", 1, None),
            Assignment(2, "N", "RSR", 1, "2"),
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.csv"
            export_roster_matrix_csv(path, scenario, assignments)
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        assert rows[0]["D01"] == "N"
        assert rows[0]["D02"] == "NO"
        assert rows[0]["D03"] == "O"
        assert rows[1]["D01"] == "O"
        assert rows[1]["D02"] == "L"
        assert rows[1]["D03"] == "N"

    def test_roster_matrix_xlsx_contains_openxml_parts(self):
        controllers = (Controller("1", "Controller", ("RSR",)),)
        scenario = Scenario(
            controllers=controllers,
            slots=build_slots(1, {"M": {"RSR": 1}}),
            role_names=("RSR",),
            max_controllers=1,
        )
        assignments = [Assignment(0, "M", "RSR", 1, "1")]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.xlsx"
            export_roster_matrix_xlsx(path, scenario, assignments)
            with ZipFile(path) as workbook:
                names = set(workbook.namelist())
                worksheet = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")

        assert "[Content_Types].xml" in names
        assert "xl/workbook.xml" in names
        assert "xl/worksheets/sheet1.xml" in names
        assert "Controller" in worksheet
        assert "M" in worksheet


try:
    import unittest
except ModuleNotFoundError:
    unittest = None


if unittest is not None:
    class TestExport(unittest.TestCase, ExportTests):
        pass


def test_roster_matrix_uses_shift_leave_night_off_and_off_codes():
    ExportTests().test_roster_matrix_uses_shift_leave_night_off_and_off_codes()


def test_roster_matrix_xlsx_contains_openxml_parts():
    ExportTests().test_roster_matrix_xlsx_contains_openxml_parts()
