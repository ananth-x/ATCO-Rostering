# ATCO Rostering Recovery

This implementation separates safety from optimization.

- Hard constraints are enforced in `ATCRosteringEnv.valid_action_mask()`.
- The same constraints are checked again by `validate_assignments()`.
- A greedy baseline is included so the pipeline can generate a legal roster before RL training is added.
- `MaskablePPO` can be trained against `ATCRosteringEnv.action_masks()`; padded controller slots let one model handle changing staff counts up to `Scenario.max_controllers`.

## Commands

Analyze historical workbook sheets:

```bash
python3 -m atco_roster.cli analyze-workbook "2024 ROSTER FINAL.xlsx"
```

Generate a 10-day baseline roster from workbook controllers:

```bash
python3 -m atco_roster.cli generate-greedy "2024 ROSTER FINAL.xlsx" --days 10 --sick-rate 0.1
```

Outputs are written to `outputs/atco_roster/`.

## RL Use

Install the optional RL dependencies:

```bash
python3 -m pip install -r requirements-atco.txt
```

Use `ATCRosteringEnv` with `sb3_contrib.MaskablePPO` and the environment's
`action_masks()` method. Do not replace hard masks with reward penalties.
