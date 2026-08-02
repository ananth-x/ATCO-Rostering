# Research Plan

## Research Question

Can a hard-masked reinforcement-learning scheduler generate ATCO first-level
rosters with zero safety violations while improving coverage and fairness under
dynamic staff availability?

## MDP Formulation

State:

- current slot position in the planning horizon;
- current day;
- current role/shift requirement;
- per-controller rest, qualification, absence, currency, consecutive-day, total-hour,
  and already-assigned-today features.

Action:

- choose one controller for the current slot;
- or choose `EMPTY` when no safe assignment is possible.

Hard mask:

- blocks absence, qualification, currency, rest, consecutive-day, and duplicate-day violations.

Reward:

- positive reward for filling a slot;
- negative reward for empty slots;
- fairness penalty for diverging from average hours.

## Baselines

- Greedy hard-masked assignment sorted by current hours and recent workload.
- Future exact optimization baseline: CP-SAT or MILP for small scenarios.
- Future ablations: RL without fairness reward, RL with different absence rates,
  RL with and without curriculum.

## Metrics

- hard violations: must be zero;
- coverage percentage;
- empty slots;
- total hours per controller;
- workload standard deviation;
- max consecutive days;
- unavailable-assignment count;
- qualification-violation count;
- runtime and training timesteps.

## Experiment Grid

Initial reproducible grid:

- horizons: 10, 14, and 30 days;
- sick rates: 0.0, 0.1, 0.2, 0.3;
- random seeds: at least 10 per setting;
- compare greedy baseline versus trained MaskablePPO.

Current implemented baseline command:

```bash
python3 -m atco_roster.cli evaluate-greedy "2024 ROSTER FINAL.xlsx" --days 10 --seeds 10
```

## Publication Notes

The workbook contains operational and personal data. Before publication:

- anonymize controller identifiers and names;
- publish synthetic scenarios or aggregated metrics unless explicit data clearance is obtained;
- report exact hard constraints and validation logic;
- include baseline comparisons, not just RL reward curves.
