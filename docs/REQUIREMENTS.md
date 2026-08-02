# Reconstructed Requirements

## Expected Output

The sample workbook shows that the first-level deliverable is a duty roster:

- rows: ATCOs/controllers
- columns: calendar dates
- cell values: duty codes such as `M`, `A`, `N`, `NO`, `O`, `G`, `L`, `CL`, `EL`, `RH`, `MED`, `COM`, `T`, `CH`

The algorithm should generate the first-level roster before trying to solve
second-level channel/position rotations inside a shift.

## Duty Codes

- `M`: Morning
- `A`: Afternoon
- `N`: Night
- `NO`: Night off after night duty
- `O`: clear off/rest day
- `G`: general duty
- `L`, `CL`, `EL`, `RH`, `MED`: leave categories
- `COM` or `COFF`: compensatory off
- `T`: training/tour
- `CH`: closed holiday

## Rating Hierarchy

The project notes define rating inheritance:

- `RSR` can work `RSR`, `ASR`, `ACC`, `ADC`, `FDP`
- `ASR` can work `ASR`, `ACC`, `ADC`, `FDP`
- `ACC` can work `ACC`, `ADC`, `FDP`
- `ADC` can work `ADC`, `FDP`
- `FDP` can work `FDP`

The workbook also uses `P` for planning, `A` for assistant, and `T` for
training/tour.

## Hard Constraints

These must be enforced by action masks and verified independently:

- Do not assign an unavailable controller.
- Do not assign a controller to a role they are not qualified for.
- Do not assign a controller whose role currency has expired.
- Enforce at least 12 hours of rest between assigned shifts.
- Do not work more than the configured consecutive-day limit.
- Do not assign the same controller twice on one calendar day in the first-level roster.

## Demand Configuration

Manpower is station-specific and must be input-driven. The code supports named
demand profiles and JSON demand matrices.

Implemented profiles:

- `conservative`: small smoke-test demand for rapid development.
- `aai_sample`: 24 controllers per operational shift, based on the project note
  that describes 4 RSR, 2 ASR, 6 tower, 6 planning, and 6 assistant positions.

Custom demand JSON shape:

```json
{
  "M": {"RSR": 4, "ASR": 2, "ADC": 6, "P": 6, "A": 6},
  "A": {"RSR": 4, "ASR": 2, "ADC": 6, "P": 6, "A": 6},
  "N": {"RSR": 4, "ASR": 2, "ADC": 6, "P": 6, "A": 6}
}
```

## Soft Constraints

These should be optimized, not used to make an invalid roster valid:

- Minimize empty slots.
- Balance total work hours.
- Prefer stable shift/team patterns when possible.
- Avoid late-to-early transitions beyond the hard minimum rest rule.

## Scope Split

First-level roster:

- assigns controller/day/shift/role slots.
- uses `M`, `A`, `N`, rest, leave, and general-duty patterns.

Second-level intra-shift rotation:

- assigns controllers to channels/working positions inside a shift.
- must handle no more than two hours on one channel, usual 90-minute seatings,
  and breaks.
- should be handled after first-level roster validity is solved.
