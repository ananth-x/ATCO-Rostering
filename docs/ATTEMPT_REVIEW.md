# Existing Attempt Review

## `ATC_Solution_Ananth.ipynb`

What it does:

- builds a `gymnasium` environment;
- uses `MaskablePPO`;
- masks some invalid controller assignments;
- simulates absenteeism, rest, qualifications, currency, and consecutive-day rules.

Main issues:

- controllers are randomly generated, not loaded from `2024 ROSTER FINAL.xlsx`;
- shift indices are generic and do not map cleanly to `M/A/N/NO/O`;
- the night-shift logic is inconsistent with the workbook legend;
- demand is `staff_per_shift`, not a role/rating requirement matrix;
- reports are printed text, not reusable experiment artifacts;
- no independent validator exists outside the environment.

Conclusion:

- useful as a proof of concept for action masking;
- not enough for operational or research claims.

## `Scheduler-Using-Reinforcement-Learning`

What it does:

- contains one environment for assigning synthetic workers to synthetic `r1..r8` ratings;
- contains another PPO environment for minute-by-minute work/break decisions;
- exports sample CSVs and visualizations.

Main issues:

- uses synthetic `CTL###` workers, not workbook ATCOs;
- uses synthetic ratings that do not match `RSR/ASR/ACC/ADC/FDP/P/A/T`;
- does not produce calendar duty rosters;
- mixes first-level team assignment with second-level break scheduling;
- generated outputs do not match the AAI sample workbook format.

Conclusion:

- useful for exploring RL mechanics;
- not a direct solution to the AAI first-level rostering problem.

## Current Direction

Use reinforcement learning only after making hard constraints explicit:

- `ATCRosteringEnv.valid_action_mask()` blocks invalid actions.
- `validate_assignments()` independently checks final rosters.
- `generate_greedy_roster()` provides a deterministic baseline.
- `train-rl` trains `MaskablePPO` against the same hard masks.
