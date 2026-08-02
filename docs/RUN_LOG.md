# Run Log

## 2026-08-02

Environment:

- Python system environment has no `numpy`.
- Optional RL dependencies were installed in local `.venv/`.

Verified commands:

```bash
python3 -m unittest discover -s tests
```

Result:

- 4 tests passed.

```bash
python3 -m atco_roster.cli generate-greedy "2024 ROSTER FINAL.xlsx" --days 10 --demand-profile aai_sample --sick-rate 0.1
```

Result:

- 648/720 slots filled.
- 0 hard violations.

```bash
python3 -m atco_roster.cli evaluate-greedy "2024 ROSTER FINAL.xlsx" --days 5 --demand-profile aai_sample --sick-rate 0.0 --sick-rate 0.1 --seeds 2
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

Current limitations:

- RL has only been smoke-tested, not trained long enough for research-quality results.
- AAI sample demand is a reconstructed profile from notes, not an officially signed-off station demand matrix.
- The first-level roster is implemented; second-level intra-shift channel rotation is documented but not solved yet.
- The generated first-level roster matrix is CSV, not yet an `.xlsx` workbook styled exactly like the historical file.
