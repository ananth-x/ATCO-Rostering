from __future__ import annotations

from .models import Assignment
from .rl_env import ATCRosteringEnv


def generate_greedy_roster(env: ATCRosteringEnv) -> list[Assignment]:
    """Generate a legal baseline roster using the same action mask as RL."""

    env.reset()
    done = False
    while not done:
        mask = env.valid_action_mask()
        candidates = [idx for idx, allowed in enumerate(mask[:-1]) if allowed]
        if candidates:
            candidates.sort(
                key=lambda idx: (
                    env.total_hours[idx],
                    env.consecutive_days[idx],
                    -env.last_end[idx],
                    env.controllers[idx].controller_id,
                )
            )
            action = candidates[0]
        else:
            action = env.empty_action
        result = env.step(action)
        done = result[2]
    return list(env.assignments)
