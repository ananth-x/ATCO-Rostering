from atco_roster.greedy import generate_greedy_roster
from atco_roster.models import Controller, Scenario, build_slots
from atco_roster.rl_env import ATCRosteringEnv
from atco_roster.validation import validate_assignments


class ATCORosterTests:
    def test_greedy_roster_respects_hard_constraints(self):
        controllers = (
            Controller("1", "RSR One", ("RSR", "ASR", "P", "A")),
            Controller("2", "RSR Two", ("RSR", "ASR", "P", "A"), frozenset({1})),
            Controller("3", "Planner", ("P",)),
            Controller("4", "Assistant", ("A",)),
            Controller("5", "Assistant Two", ("A",)),
            Controller("6", "Planner Two", ("P",)),
        )
        demand = {
            "M": {"RSR": 1, "P": 1, "A": 1},
            "N": {"RSR": 1, "P": 1, "A": 1},
        }
        scenario = Scenario(
            controllers=controllers,
            slots=build_slots(3, demand),
            role_names=("A", "P", "RSR"),
            max_controllers=8,
        )
        env = ATCRosteringEnv(scenario)
        assignments = generate_greedy_roster(env)
        report = validate_assignments(scenario, assignments)

        assert report.is_valid
        assert len(assignments) == len(scenario.slots)
        assert not any(
            assignment.controller_id == "2" and assignment.day == 1 for assignment in assignments
        )


try:
    import unittest
except ModuleNotFoundError:
    unittest = None


if unittest is not None:
    class TestATCORoster(unittest.TestCase, ATCORosterTests):
        pass


def test_greedy_roster_respects_hard_constraints():
    ATCORosterTests().test_greedy_roster_respects_hard_constraints()
