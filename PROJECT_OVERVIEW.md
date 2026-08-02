# ATCO Rostering Project Overview

This file is the simple, current explanation of what I understand, what the
project is trying to solve, and what the code now does.

## What I Understood

The project is for generating Air Traffic Control Officer rosters for the
Airport Authority of India context.

The original requirements were vague, but the project files show two levels of
scheduling:

1. First-level roster: decide each controller's daily duty code, such as
   `M`, `A`, `N`, `NO`, `O`, `G`, `L`.
2. Second-level intra-shift rotation: inside a shift, decide which controller
   sits on which channel/position and when they take breaks.

The workbook examples mainly ask for the first-level roster first. The current
implementation focuses on that.

## Main Goal

Build a defensible rostering system that:

- reads the historical roster workbook;
- uses real controller ratings from the workbook;
- enforces ATC safety rules as hard constraints;
- can generate a valid roster;
- can train a reinforcement-learning agent to improve over a baseline;
- exports results in files that can be inspected and compared.

## Inputs

Current important inputs:

- `project_goals.txt`: original requirement notes.
- `2024 ROSTER FINAL.xlsx`: historical sample rosters and controller data.
- `ATC_Solution_Ananth.ipynb`: earlier notebook attempt using MaskablePPO.
- `Scheduler-Using-Reinforcement-Learning/`: earlier RL package, kept as a submodule.

The workbook contains monthly duty sheets with:

- employee IDs;
- controller names;
- ratings;
- shift/team labels;
- daily duty codes.

## Outputs

The current commands generate:

- `generated_roster.csv`: slot-level assignment output.
- `generated_roster_matrix.csv`: first-level duty matrix like the workbook.
- `generated_roster_matrix.xlsx`: Excel-readable first-level duty matrix.
- `validation_report.json`: independent hard-constraint validation report.

For RL runs, the same outputs are prefixed with `rl_`, and the trained model is
also saved.

## Duty Codes

Important first-level duty codes:

- `M`: Morning
- `A`: Afternoon
- `N`: Night
- `NO`: Night off after night
- `O`: clear off/rest
- `G`: general duty
- `L`, `CL`, `EL`, `RH`, `MED`: leave-related codes
- `COM` or `COFF`: compensatory off
- `T`: training/tour
- `CH`: closed holiday

## Hard Constraints

These are safety rules. The system must not violate them.

- Do not assign unavailable staff.
- Do not assign a controller to a role they are not qualified for.
- Do not assign a controller if their role currency is expired.
- Maintain at least 12 hours rest between shifts.
- Do not exceed the configured maximum consecutive work days.
- Do not assign the same controller twice on one day in the first-level roster.

Hard constraints are enforced twice:

- during generation through action masks;
- after generation through an independent validator.

## Soft Goals

These are optimization goals. They matter, but they cannot override safety.

- Fill as many required slots as possible.
- Balance workload across controllers.
- Avoid bad shift patterns when possible.
- Keep outputs comparable across many experiment seeds.

## Why Reinforcement Learning

RL can make sense because each assignment affects future choices. For example,
assigning someone to a night shift today affects whether they can work tomorrow.

However, RL alone is not safe enough for ATC rostering. A reward penalty is not
enough for safety-critical rules. That is why the current system uses
`MaskablePPO`: invalid actions are blocked before the agent can choose them.

The research idea is:

> Can hard-masked RL generate zero-violation ATCO rosters while improving
> coverage and fairness under changing availability?

## Current Implementation

The clean implementation is in `atco_roster/`.

Important modules:

- `workbook.py`: reads useful data from the historical workbook.
- `models.py`: shared dataclasses and rating hierarchy.
- `rl_env.py`: hard-masked ATCO rostering environment.
- `greedy.py`: deterministic baseline generator.
- `validation.py`: independent safety validator.
- `export.py`: CSV/JSON/XLSX exports.
- `rl_train.py`: MaskablePPO training command.
- `evaluate.py`: baseline experiment metrics.

## How To Run Locally

Use the local virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-atco.txt
```

Run tests:

```bash
.venv/bin/python -m unittest discover -s tests
```

Generate a conservative 10-day roster:

```bash
.venv/bin/python -m atco_roster.cli generate-greedy "2024 ROSTER FINAL.xlsx" --days 10 --sick-rate 0.1
```

Generate with the reconstructed AAI sample demand:

```bash
.venv/bin/python -m atco_roster.cli generate-greedy "2024 ROSTER FINAL.xlsx" --days 10 --demand-profile aai_sample --sick-rate 0.1
```

Run a short RL smoke test:

```bash
.venv/bin/python -m atco_roster.cli train-rl "2024 ROSTER FINAL.xlsx" --days 2 --timesteps 64 --n-steps 64 --sick-rate 0.1
```

## GitHub Hygiene

Tracked files should be source code, tests, documentation, original project
evidence, and dependency manifests.

Ignored files include:

- `.venv/`
- `outputs/`
- `__pycache__/`
- `.pytest_cache/`
- generated model/output files from the old RL submodule

Important caution:

The historical workbook contains real-looking operational/personnel data. It is
currently tracked because it is the main evidence source for this recovery
project. If the GitHub repository is public or the data is sensitive, the right
next step is to remove/anonymize it and rewrite git history.

## Current Limitations

- The RL path has been smoke-tested, not fully trained for research-quality results.
- The AAI sample demand profile is reconstructed from notes, not officially validated.
- The `.xlsx` export is functional but not styled exactly like the historical workbook.
- Second-level intra-shift channel rotation is not implemented yet.
- Medical/ELP expiry and leave applications are documented but not fully modeled from structured inputs yet.

## Next Practical Steps

1. Confirm whether the workbook data can remain in GitHub.
2. Confirm the exact station demand matrix to use.
3. Add structured leave/medical/ELP input files.
4. Train RL across multiple seeds and compare against the greedy baseline.
5. Add a small exact-optimization baseline for research comparison.
6. Improve Excel formatting to match the historical roster workbook.
