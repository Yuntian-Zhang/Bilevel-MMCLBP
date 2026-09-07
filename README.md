# Bilevel-MMCLBP

This repository is a reproducibility package for the computational study in
*An Exact Algorithm for the Max--Min Covering Location Blocker Problem* by
Yun-Tian Zhang, Fabio Furini, Ivana Ljubić, and Chen Chen. It implements the
outer value-function decomposition and the two follower variants used in the
paper: a direct MILP and branch-and-Benders-cut with closed-form separation.

## Cite

If you use this code, please cite the associated manuscript and identify this
repository by its commit hash. A permanent software citation will be added
when the archival version is released.

```bibtex
@software{zhang2026bilevelmmclbp,
  author = {Zhang, Yun-Tian and Furini, Fabio and Ljubić, Ivana and Chen, Chen},
  title = {Bilevel-MMCLBP: Replication Code for the Max--Min Covering Location Blocker Problem},
  year = {2026},
  url = {https://github.com/Yuntian-Zhang/Bilevel-MMCLBP}
}
```

## Requirements

- Python 3.10 or later;
- a C++17-compatible compiler;
- Gurobi Optimizer 13.x with a valid license;
- Python packages listed in `requirements.txt`.

The experiments in the manuscript used Gurobi 13.0.1. The package was also
validated with Gurobi 13.0.3, NumPy 2.2.6, pybind11 3.1.0, and Python 3.10.
Running times can differ across hardware and solver versions; optimal
objectives are the primary replication target.

## Install

Create and activate a Python environment, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

On Debian or Ubuntu, install the `python3-venv` system package first if the
first command reports that `ensurepip` is unavailable.

The second command compiles the C++17 separation extension `fast_sep`. To
check the installation, run:

```bash
python3 -c "import fast_sep; print('fast_sep imported successfully')"
```

## Quick start

Run a small closed-form Benders instance:

```bash
python3 main.py 5 30 4 8 0.7 1 0 --timelimit 30
```

Or run the full smoke test, which compares the Benders follower, the direct
MILP follower, and brute-force enumeration on small instances:

```bash
make smoke
```

## Reproducing the experiments

Each command writes a timestamped CSV file under `results/generated/`.

| Paper result | Command | Scope |
| --- | --- | --- |
| Small exactness check | `make smoke` | Three small instances; seconds |
| Main synthetic benchmark | `python3 scripts/reproduce_main_table.py --full` | 65 instances per follower variant; up to one hour per run |
| Quick synthetic check | `python3 scripts/reproduce_main_table.py --quick` | Six final-algorithm runs; under a minute on the validation machine |
| Value-function coefficients | `python3 scripts/reproduce_coefficient_ablation.py` | Nine diagnostic instances and three coefficient choices |
| Virginia Beach case study | `python3 scripts/reproduce_virginia_beach.py` | 40 bases and 2,706 OHCA events |

Use `--help` on any script to inspect its options. The benchmark generator and
the command-line interface are in `main.py`; the reproducibility scripts keep
the parameter grids and output formats separate from the solver code.

## Repository contents

- `data/`: synthetic instance generator and the Virginia Beach replication
  workbook with attribution and licensing information;
- `solver/`: outer master problem, direct follower MILP, and Benders follower;
- `fast_sep.cpp`: C++17 closed-form Benders separation routine;
- `scripts/`: reproducible experiment entry points;
- `tests/`: exactness checks for the implementation;
- `docs/`: experiment design and reproducibility notes;
- `results/`: generated outputs are written locally and excluded from version
  control.

## Support

Please open an issue in this repository with the command, operating system,
Python version, Gurobi version, and complete error output.

## License

The code is distributed under the [MIT License](LICENSE). The Virginia Beach
data retain their own upstream attribution and license in
`data/virginia_beach/`.
