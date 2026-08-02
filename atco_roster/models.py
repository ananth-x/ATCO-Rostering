from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


RATING_HIERARCHY = {
    "RSR": ("RSR", "ASR", "ACC", "ADC", "FDP"),
    "ASR": ("ASR", "ACC", "ADC", "FDP"),
    "ACC": ("ACC", "ADC", "FDP"),
    "ADC": ("ADC", "FDP"),
    "FDP": ("FDP",),
    "P": ("P",),
    "A": ("A",),
    "T": ("T",),
}


@dataclass(frozen=True)
class Controller:
    controller_id: str
    name: str
    qualifications: tuple[str, ...]
    unavailable_days: frozenset[int] = frozenset()
    days_since_role: Mapping[str, int] = field(default_factory=dict)

    @classmethod
    def from_rating(
        cls,
        controller_id: str,
        name: str,
        rating: str,
        unavailable_days: frozenset[int] = frozenset(),
    ) -> "Controller":
        rating = normalize_code(rating)
        return cls(
            controller_id=str(controller_id),
            name=name.strip(),
            qualifications=RATING_HIERARCHY.get(rating, (rating,)),
            unavailable_days=unavailable_days,
        )


@dataclass(frozen=True)
class ShiftSlot:
    day: int
    shift: str
    role: str
    slot_number: int
    start_hour: float
    duration_hours: float

    @property
    def end_hour(self) -> float:
        return self.start_hour + self.duration_hours


@dataclass(frozen=True)
class Assignment:
    day: int
    shift: str
    role: str
    slot_number: int
    controller_id: str | None


@dataclass(frozen=True)
class Scenario:
    controllers: tuple[Controller, ...]
    slots: tuple[ShiftSlot, ...]
    role_names: tuple[str, ...]
    max_controllers: int
    min_rest_hours: float = 12.0
    max_consecutive_days: int = 4
    currency_threshold_days: int = 50
    night_recovery_days: int = 2


def normalize_code(value: object) -> str:
    return str(value or "").strip().upper()


def default_shift_times() -> dict[str, tuple[float, float]]:
    # Based on the project notes: morning 6h, afternoon 6.5h, night 11.5h.
    return {
        "M": (6.0, 6.0),
        "A": (13.0, 6.5),
        "N": (20.0, 11.5),
    }


def build_slots(
    days: int,
    demand_by_shift_role: Mapping[str, Mapping[str, int]],
    shift_times: Mapping[str, tuple[float, float]] | None = None,
) -> tuple[ShiftSlot, ...]:
    shift_times = shift_times or default_shift_times()
    slots: list[ShiftSlot] = []
    for day in range(days):
        for shift, role_counts in demand_by_shift_role.items():
            if shift not in shift_times:
                raise ValueError(f"Missing start/duration for shift {shift!r}")
            start, duration = shift_times[shift]
            absolute_start = day * 24.0 + start
            for role, count in role_counts.items():
                for slot_number in range(1, int(count) + 1):
                    slots.append(
                        ShiftSlot(
                            day=day,
                            shift=shift,
                            role=normalize_code(role),
                            slot_number=slot_number,
                            start_hour=absolute_start,
                            duration_hours=duration,
                        )
                    )
    return tuple(slots)
