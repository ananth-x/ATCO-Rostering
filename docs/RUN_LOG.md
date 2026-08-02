# Run Log

## 2026-08-02

Environment:

- All verification below was run through local `.venv/`.
- Optional RL dependencies are installed in `.venv/` from `requirements-atco.txt`.

Verified commands:

```bash
.venv/bin/python -m unittest discover -s tests
```

Result:

- 6 tests passed.

```bash
.venv/bin/python -m atco_roster.cli generate-greedy "2024 ROSTER FINAL.xlsx" --days 10 --sick-rate 0.1
```

Result:

- 190/190 slots filled.
- 0 hard violations.
- wrote `generated_roster.csv`, `generated_roster_matrix.csv`,
  `generated_roster_matrix.xlsx`, and `validation_report.json`.

```bash
.venv/bin/python -m atco_roster.cli generate-greedy "2024 ROSTER FINAL.xlsx" --days 5 --demand-profile aai_sample --sick-rate 0.1
```

Result:

- 321/360 slots filled.
- 0 hard violations.
- wrote `generated_roster.csv`, `generated_roster_matrix.csv`,
  `generated_roster_matrix.xlsx`, and `validation_report.json`.

```bash
.venv/bin/python -m atco_roster.cli evaluate-greedy "2024 ROSTER FINAL.xlsx" --days 5 --demand-profile aai_sample --sick-rate 0.0 --sick-rate 0.1 --seeds 2
```

Result:

- 4/4 runs hard-valid.
- average coverage: 0.906.

```bash
.venv/bin/python -m atco_roster.cli train-rl "2024 ROSTER FINAL.xlsx" --days 2 --timesteps 64 --n-steps 64 --sick-rate 0.1
```

Result:

- 38/38 slots filled.
- 0 hard violations.
- `rl_validation_report.json` reported `is_valid: true`.
- wrote `rl_generated_roster.csv`, `rl_generated_roster_matrix.csv`,
  `rl_generated_roster_matrix.xlsx`, `rl_validation_report.json`, and a model zip.

Current limitations:

- RL has only been smoke-tested, not trained long enough for research-quality results.
- AAI sample demand is a reconstructed profile from notes, not an officially signed-off station demand matrix.
- The first-level roster is implemented; second-level intra-shift channel rotation is documented but not solved yet.
- The generated first-level roster matrix is now available as CSV and `.xlsx`;
  the `.xlsx` is functional but not yet styled exactly like the historical workbook.
