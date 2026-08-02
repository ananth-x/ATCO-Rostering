from atco_roster.metrics import summarize_report
from atco_roster.validation import ValidationReport


class MetricsTests:
    def test_summarize_report_calculates_coverage_and_workload(self):
        report = ValidationReport(
            total_slots=4,
            filled_slots=3,
            empty_slots=1,
            hard_violations=(),
            hours_by_controller={"a": 6.0, "b": 12.0},
            coverage_by_shift_role={},
        )

        summary = summarize_report(report)

        assert summary["coverage"] == 0.75
        assert summary["hard_violations"] == 0
        assert summary["mean_hours"] == 9.0
        assert summary["std_hours"] == 3.0


try:
    import unittest
except ModuleNotFoundError:
    unittest = None


if unittest is not None:
    class TestMetrics(unittest.TestCase, MetricsTests):
        pass


def test_summarize_report_calculates_coverage_and_workload():
    MetricsTests().test_summarize_report_calculates_coverage_and_workload()
