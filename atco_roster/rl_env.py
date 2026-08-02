from __future__ import annotations

from collections import defaultdict
import random
from typing import Any

try:
    import numpy as np
except ModuleNotFoundError:
    class _NumpyFallback:
        bool = bool
        float32 = float

        @staticmethod
        def zeros(size: int, dtype: object = bool) -> list:
            return [False for _ in range(size)]

        @staticmethod
        def array(values: list[float], dtype: object = float) -> list[float]:
            return values

        @staticmethod
        def random_seed(seed: int) -> None:
            return None

    np = _NumpyFallback()

from .models import Assignment, Scenario, normalize_code

try:
    import gymnasium as gym
    from gymnasium import spaces
except ModuleNotFoundError:  # Core validator/generator can run without RL deps.
    gym = None
    spaces = None


BaseEnv = gym.Env if gym is not None else object


class ATCRosteringEnv(BaseEnv):
    """Hard-masked ATCO roster environment.

    The agent chooses one controller for the current slot, or the final action
    for EMPTY. Hard rules are implemented in valid_action_mask/action_masks.
    """

    metadata = {"render_modes": []}

    def __init__(self, scenario: Scenario):
        if gym is not None:
            super().__init__()
        self.scenario = scenario
        self.empty_action = scenario.max_controllers
        self.controllers = list(scenario.controllers)
        self.controller_index = {
            controller.controller_id: idx for idx, controller in enumerate(self.controllers)
        }
        self.role_index = {role: idx for idx, role in enumerate(scenario.role_names)}
        self.max_roles = max(1, len(scenario.role_names))
        self.features_per_controller = 8

        self.action_space = (
            spaces.Discrete(scenario.max_controllers + 1) if spaces is not None else None
        )
        self.observation_space = (
            spaces.Box(
                low=0.0,
                high=1.0,
                shape=(3 + scenario.max_controllers * self.features_per_controller,),
                dtype=np.float32,
            )
            if spaces is not None
            else None
        )
        self.reset()

    def reset(self, seed: int | None = None, options: dict[str, Any] | None = None):
        if seed is not None:
            random.seed(seed)
            if hasattr(np, "random"):
                np.random.seed(seed)
        self.current_step = 0
        self.assignments: list[Assignment] = []
        self.last_end = [-9999.0] * len(self.controllers)
        self.last_day = [-9999] * len(self.controllers)
        self.last_night_day = [-9999] * len(self.controllers)
        self.consecutive_days = [0] * len(self.controllers)
        self.total_hours = [0.0] * len(self.controllers)
        self.days_since_role = [
            defaultdict(int, controller.days_since_role) for controller in self.controllers
        ]
        if gym is not None:
            return self._observation(), {}
        return self._observation()

    def valid_action_mask(self) -> np.ndarray:
        mask = np.zeros(self.scenario.max_controllers + 1, dtype=bool)
        if self.current_step >= len(self.scenario.slots):
            mask[self.empty_action] = True
            return mask

        slot = self.scenario.slots[self.current_step]
        mask[self.empty_action] = True
        already_assigned_today = {
            assignment.controller_id
            for assignment in self.assignments
            if assignment.day == slot.day and assignment.controller_id is not None
        }

        for idx, controller in enumerate(self.controllers):
            if idx >= self.scenario.max_controllers:
                break
            if controller.controller_id in already_assigned_today:
                continue
            if slot.day in controller.unavailable_days:
                continue
            if 0 < slot.day - self.last_night_day[idx] <= self.scenario.night_recovery_days:
                continue
            if slot.role not in controller.qualifications:
                continue
            if self.days_since_role[idx][slot.role] >= self.scenario.currency_threshold_days:
                continue
            if slot.start_hour - self.last_end[idx] < self.scenario.min_rest_hours:
                continue
            if (
                self.last_day[idx] == slot.day - 1
                and self.consecutive_days[idx] >= self.scenario.max_consecutive_days
            ):
                continue
            mask[idx] = True
        return mask

    def action_masks(self) -> np.ndarray:
        return self.valid_action_mask()

    def step(self, action: int):
        slot = self.scenario.slots[self.current_step]
        mask = self.valid_action_mask()
        if action < 0 or action >= len(mask) or not mask[action]:
            action = self.empty_action

        reward = -25.0
        controller_id: str | None = None
        if action != self.empty_action:
            controller = self.controllers[action]
            controller_id = controller.controller_id
            reward = 10.0
            if self.last_day[action] == slot.day - 1:
                self.consecutive_days[action] += 1
            elif self.last_day[action] != slot.day:
                self.consecutive_days[action] = 1
            self.last_day[action] = slot.day
            if slot.shift == "N":
                self.last_night_day[action] = slot.day
            self.last_end[action] = slot.end_hour
            self.total_hours[action] += slot.duration_hours
            self.days_since_role[action][slot.role] = 0

            average = sum(self.total_hours) / max(1, len(self.total_hours))
            reward -= abs(self.total_hours[action] - average) * 0.05

        self.assignments.append(
            Assignment(slot.day, slot.shift, slot.role, slot.slot_number, controller_id)
        )
        self.current_step += 1
        if self._day_finished():
            for role_days in self.days_since_role:
                for role in self.scenario.role_names:
                    role_days[role] += 1

        done = self.current_step >= len(self.scenario.slots)
        if gym is not None:
            return self._observation(), reward, done, False, {}
        return self._observation(), reward, done, {}

    def _day_finished(self) -> bool:
        if self.current_step == 0 or self.current_step >= len(self.scenario.slots):
            return True
        previous_day = self.scenario.slots[self.current_step - 1].day
        current_day = self.scenario.slots[self.current_step].day
        return previous_day != current_day

    def _observation(self) -> np.ndarray:
        if self.current_step >= len(self.scenario.slots):
            slot = self.scenario.slots[-1]
            slot_progress = 1.0
        else:
            slot = self.scenario.slots[self.current_step]
            slot_progress = self.current_step / max(1, len(self.scenario.slots))

        obs = [
            slot_progress,
            slot.day / max(1, self.scenario.slots[-1].day + 1),
            self.role_index.get(normalize_code(slot.role), 0) / self.max_roles,
        ]
        for idx in range(self.scenario.max_controllers):
            if idx >= len(self.controllers):
                obs.extend([0.0] * self.features_per_controller)
                continue
            controller = self.controllers[idx]
            rest = min(72.0, max(0.0, slot.start_hour - self.last_end[idx])) / 72.0
            qualified = 1.0 if slot.role in controller.qualifications else 0.0
            absent = 1.0 if slot.day in controller.unavailable_days else 0.0
            night_recovery = (
                1.0
                if 0 < slot.day - self.last_night_day[idx] <= self.scenario.night_recovery_days
                else 0.0
            )
            currency = min(
                self.scenario.currency_threshold_days,
                self.days_since_role[idx][slot.role],
            ) / max(1, self.scenario.currency_threshold_days)
            consecutive = self.consecutive_days[idx] / max(1, self.scenario.max_consecutive_days)
            hours = min(72.0, self.total_hours[idx]) / 72.0
            already_today = any(
                assignment.day == slot.day and assignment.controller_id == controller.controller_id
                for assignment in self.assignments
            )
            obs.extend(
                [rest, qualified, absent, night_recovery, currency, consecutive, hours, float(already_today)]
            )
        return np.array(obs, dtype=np.float32)
