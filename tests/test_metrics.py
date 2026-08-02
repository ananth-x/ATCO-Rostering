import json
from pathlib import Path
import tempfile

from atco_roster.evaluate import evaluate_config
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

    def test_evaluate_config_writes_greedy_metrics(self):
        config = {
            "days": 1,
            "demand": {"M": {"RSR": 1}},
            "controllers": [
                {"id": "C001", "name": "Controller 001", "rating": "RSR"},
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "scenario.json"
            output_dir = Path(directory) / "metrics"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            rows = evaluate_config(
                config_path,
                seeds=[0],
                output_dir=output_dir,
                rl_timesteps=0,
                include_rl=False,
            )

            assert rows[0]["method"] == "greedy"
            assert rows[0]["coverage"] == 1.0
            assert (output_dir / "config_metrics.csv").exists()
            assert (output_dir / "config_metrics.json").exists()


try:
    import unittest
except ModuleNotFoundError:
    unittest = None


if unittest is not None:
    class TestMetrics(unittest.TestCase, MetricsTests):
        pass


def test_summarize_report_calculates_coverage_and_workload():
    MetricsTests().test_summarize_report_calculates_coverage_and_workload()


def test_evaluate_config_writes_greedy_metrics():
    MetricsTests().test_evaluate_config_writes_greedy_metrics()
