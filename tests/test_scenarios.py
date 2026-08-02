from atco_roster.scenarios import demand_profile, normalize_demand


class ScenarioTests:
    def test_demand_profile_contains_aai_sample_shift_size(self):
        demand = demand_profile("aai_sample")
        assert sum(demand["M"].values()) == 24
        assert sum(demand["A"].values()) == 24
        assert sum(demand["N"].values()) == 24

    def test_normalize_demand_uppercases_and_drops_zero_counts(self):
        demand = normalize_demand({"m": {"rsr": 2, "p": 0}})
        assert demand == {"M": {"RSR": 2}}


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
