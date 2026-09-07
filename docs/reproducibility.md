# Reproducibility guide

## Computational environment

The manuscript experiments use Python, Gurobi, NumPy, and a C++17 extension
compiled with pybind11. The reference configuration uses a 3,600-second global
wall-clock limit per run, radii `(4, 8)`, exponential decay rate `0.5`, and
target coefficient `beta = 0.7`.

The benchmark generator uses NumPy's legacy random-state sequence through
`numpy.random.seed(seed)`. Consequently, the numerical instances are
deterministic for a fixed NumPy version and seed. Solver paths and running
times may differ across machines and Gurobi versions.

## Validation sequence

1. Install the package with `python3 -m pip install -e .`.
2. Run `make test` to compare the Benders follower with the direct MILP and
   with brute-force enumeration on a small instance.
3. Run `python3 scripts/reproduce_main_table.py --quick` to regenerate the
   six short benchmark checks.
4. Run `python3 scripts/reproduce_virginia_beach.py` to generate the case
   study result. It verifies the published unblocked objective before solving
   the blocker problem.
5. Run `python3 scripts/reproduce_main_table.py --full` for the complete main
   benchmark. This is computationally expensive because each run can use the
   full one-hour limit.

## Expected synthetic objectives

For the final Benders configuration, the first three seeds of the two compact
benchmark classes have the following optimal blocker objectives:

| Facilities | Demands | Seeds 0, 1, 2 |
| ---: | ---: | --- |
| 20 | 20,000 | 9, 5, 7 |
| 25 | 20,000 | 9, 7, 9 |

The unblocked follower value for the Virginia Beach instance is approximately
`1775.42`; the target for `beta = 0.7` is approximately `1242.80`.

The Virginia Beach workflow evaluates the unblocked follower with the exact
closed-form Benders model rather than the direct linearization. This avoids a
very large linearized model while preserving the follower optimum used to set
the target.

## Result files

Scripts write UTC-timestamped CSV files to `results/generated/`. These files
contain the complete input parameters, status, incumbent objective, bound,
gap, and elapsed time needed to regenerate aggregate tables externally.
