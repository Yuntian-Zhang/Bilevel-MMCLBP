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

## Main synthetic benchmark (Section 5.2, Table 1 and Table EC.2)

```bash
python3 scripts/reproduce_main_table.py --quick
python3 scripts/reproduce_main_table.py --full
```

`--quick` executes the two compact classes with seeds 0–2. `--full` executes
all 65 synthetic instances for each selected method. Use
`--method benders` (`OD+B&BC`) or `--method milp` (`OD+MILP`) to run one method only. Each full run
uses the supplied global time limit, 3,600 seconds by default.

## Interdiction-cut coefficients (Section 5.3, Table 2)

```bash
python3 scripts/reproduce_coefficient_ablation.py --quick
python3 scripts/reproduce_coefficient_ablation.py
```

The quick version runs the 20-by-20,000 diagnostic class. The full command
runs the three diagnostic classes, seeds 0–2, and the `global`, `nogood`, and
`critical` coefficient variants. The paper reports `nogood` (No-good) and
`critical` (Critical); `global` is an additional variant not reported there.

## Virginia Beach case study (Section 5.6)

```bash
python3 scripts/reproduce_virginia_beach.py --timelimit 3600
```

See [Virginia Beach](virginia_beach.md) for data and parameter details.

## From raw CSV to the tables of the paper

The raw result CSVs contain all inputs, solution status, objective, bound, gap,
time, and Benders statistics. They are designed to be aggregated directly into
the tables of the paper with a spreadsheet or a statistical script. The CSV
files behind the tables of the paper are in `results/`; see
[results/results.md](../results/results.md) for the correspondence.
