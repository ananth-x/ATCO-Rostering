# ATCO Rostering

This repository recovers and restructures an Air Traffic Control Officer
rostering project from historical AAI roster samples, an earlier notebook, and
an earlier reinforcement-learning prototype.

The current direction is reinforcement learning with hard safety constraints:
the agent may optimize assignments, but invalid actions are masked and the final
roster is independently validated.

## Current Artifacts

- `project_goals.txt`: original vague project notes.
- `2024 ROSTER FINAL.xlsx`: historical roster workbook used for reverse engineering.
- `ATC_Solution_Ananth.ipynb`: earlier MaskablePPO notebook prototype.
- `Scheduler-Using-Reinforcement-Learning/`: earlier RL package kept as a submodule.
- `atco_roster/`: current cleaned implementation.
- `docs/`: reconstructed requirements, attempt review, and research framing.

## Quick Start

Analyze the historical workbook:

```bash
python3 -m atco_roster.cli analyze-workbook "2024 ROSTER FINAL.xlsx"
```

Generate a 10-day hard-valid baseline roster:

```bash
python3 -m atco_roster.cli generate-greedy "2024 ROSTER FINAL.xlsx" --days 10 --sick-rate 0.1
```

Install optional RL dependencies:

```bash
python3 -m pip install -r requirements-atco.txt
```

Train the first MaskablePPO model:

```bash
python3 -m atco_roster.cli train-rl "2024 ROSTER FINAL.xlsx" --days 10 --timesteps 60000 --sick-rate 0.1
```
