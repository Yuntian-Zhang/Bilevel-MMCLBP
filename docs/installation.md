# Installation

## Requirements

- Python 3.10 or later;
- a C++17-compatible compiler;
- Gurobi Optimizer 13.x with an active license;
- the Python packages listed in `requirements.txt`.

The manuscript experiments used Gurobi 13.0.1. This package was validated with
Gurobi 13.0.3, NumPy 2.2.6, pybind11 3.1.0, and Python 3.10. Running times can
vary across machines and solver versions; optimal objectives are the primary
replication target.

## Create an environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

The editable installation compiles the C++17 extension `fast_sep`. On Debian
or Ubuntu, install `python3-venv` first if `python3 -m venv` reports that
`ensurepip` is unavailable.

## Verify the installation

```bash
python3 -c "import fast_sep; print('fast_sep imported successfully')"
make test
```

`make test` compiles the extension if needed and runs the automated exactness
checks. A Gurobi license must be available to the Python process. Do not place
license files in this repository.
