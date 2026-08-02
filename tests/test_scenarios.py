import json
from pathlib import Path
import tempfile

from atco_roster.scenarios import demand_profile, normalize_demand, scenario_from_config


class ScenarioTests:
    def test_demand_profile_contains_aai_sample_shift_size(self):
        demand = demand_profile("aai_sample")
        assert sum(demand["M"].values()) == 24
        assert sum(demand["A"].values()) == 24
        assert sum(demand["N"].values()) == 24

    def test_normalize_demand_uppercases_and_drops_zero_counts(self):
        demand = normalize_demand({"m": {"rsr": 2, "p": 0}})
        assert demand == {"M": {"RSR": 2}}

    def test_scenario_from_config_loads_dynamic_inputs(self):
        config = {
            "days": 2,
            "demand": {"M": {"RSR": 1}},
            "constraints": {
                "min_rest_hours": 10,
                "max_consecutive_days": 3,
                "currency_threshold_days": 40,
                "night_recovery_days": 1,
            },
            "controllers": [
                {
                    "id": "C001",
                    "name": "Controller",
                    "rating": "RSR",
                    "unavailable_days": [1],
                    "days_since_role": {"RSR": 5},
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scenario.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            scenario = scenario_from_config(path)

        assert len(scenario.controllers) == 1
        assert len(scenario.slots) == 2
        assert scenario.controllers[0].controller_id == "C001"
        assert scenario.controllers[0].unavailable_days == frozenset({1})
        assert scenario.controllers[0].days_since_role == {"RSR": 5}
        assert scenario.min_rest_hours == 10
        assert scenario.max_consecutive_days == 3
        assert scenario.currency_threshold_days == 40
        assert scenario.night_recovery_days == 1


try:
    import unittest
except ModuleNotFoundError:
    unittest = None


if unittest is not None:
    class TestScenario(unittest.TestCase, ScenarioTests):
        pass


def test_demand_profile_contains_aai_sample_shift_size():
    ScenarioTests().test_demand_profile_contains_aai_sample_shift_size()


def test_normalize_demand_uppercases_and_drops_zero_counts():
    ScenarioTests().test_normalize_demand_uppercases_and_drops_zero_counts()


def test_scenario_from_config_loads_dynamic_inputs():
    ScenarioTests().test_scenario_from_config_loads_dynamic_inputs()
