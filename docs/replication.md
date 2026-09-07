# Replicating the computational results

All scripts write UTC-timestamped machine-readable CSV files under
`results/generated/`. That directory is excluded from version control because
output files are regenerated locally and can be large.

## Validation run

```bash
make smoke
```

This checks three small instances against brute-force enumeration. It should
finish in seconds.

## Main synthetic benchmark

```bash
python3 scripts/reproduce_main_table.py --quick
python3 scripts/reproduce_main_table.py --full
```

`--quick` executes the two compact classes with seeds 0–2. `--full` executes
all 65 synthetic instances for each selected follower method. Use
`--method benders` or `--method milp` to run one method only. Each full run
uses the supplied global time limit, 3,600 seconds by default.

## Value-function coefficient ablation

```bash
python3 scripts/reproduce_coefficient_ablation.py --quick
python3 scripts/reproduce_coefficient_ablation.py
```

The quick version runs the 20-by-20,000 diagnostic class. The full command
runs the three diagnostic classes, seeds 0–2, and the `global`, `nogood`, and
`critical` coefficient variants.

## Case study

```bash
python3 scripts/reproduce_virginia_beach.py --timelimit 3600
```

See [Virginia Beach](virginia_beach.md) for data and parameter details.

## From raw CSV to manuscript tables

The raw result CSVs contain all inputs, solution status, objective, bound, gap,
time, and Benders statistics. They are designed to be aggregated directly into
the manuscript tables with a spreadsheet or a statistical script. Keep a
validated raw-output snapshot with the hardware and solver versions before an
archival release.
