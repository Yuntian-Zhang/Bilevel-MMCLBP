# Bilevel-MMCLBP

This repository contains the source code and computational material accompanying the paper

**“An Exact Algorithm for the Max-Min Covering Location Blocker Problem”**

by Yun-Tian Zhang, Fabio Furini, Ivana Ljubić, and Chen Chen

## Repository Structure

```text
.
├── data/
│   └── data.py
├── solver/
│   ├── bilevel_solver.py
│   ├── master_problem.py
│   └── sub_problem.py
├── fast_sep.cpp
├── setup.py
├── main.py
└── README.md
```

The main files are:

* `data/data.py`: instance generation and data preprocessing.
* `solver/master_problem.py`: leader problem and value-function cuts.
* `solver/sub_problem.py`: follower formulations and Benders callback.
* `solver/bilevel_solver.py`: iterative bilevel solution framework.
* `fast_sep.cpp`: C++ implementation of the Benders cut separation routine.
* `main.py`: script used to run the computational experiments.

## Requirements

The code requires:

* Python 3
* Gurobi Optimizer with a valid license
* NumPy
* pybind11
* setuptools
* A C++17-compatible compiler

## Compilation

The Benders separation routine is implemented in C++ and exposed to Python through pybind11.

From the root directory of the repository, compile the extension using

```bash
python setup.py build_ext --inplace
```

To force recompilation, use

```bash
python setup.py build_ext --inplace --force
```

After compilation, the installation can be checked with

```bash
python -c "import fast_sep; print('fast_sep imported successfully')"
```

The expected output is

```text
fast_sep imported successfully
```

## Reproducing the Computational Experiments

Each run is specified directly from the command line:

```bash
python main.py I J r1 r2 beta benders seed [--degeneracy {0,1}] [--timelimit SECONDS]
```

The arguments are:

* `I`: number of candidate facility locations;
* `J`: number of customers;
* `r1`: radius of full coverage;
* `r2`: maximum covering radius;
* `beta`: target coverage coefficient;
* `benders`: `0` for the original follower formulation and `1` for the Benders-based follower;
* `seed`: random seed;
* `--degeneracy`: `0` for standard Benders separation and `1` for degeneracy-enhanced separation (default: `0`);
* `--timelimit`: time limit in seconds for the bilevel solution procedure (default: `3600`).

For example, the standard Benders variant can be run as

```bash
python main.py 20 20000 4 8 0.7 1 0 --degeneracy 0 --timelimit 3600
```

The degeneracy-enhanced Benders variant can be run as

```bash
python main.py 20 20000 4 8 0.7 1 0 --degeneracy 1 --timelimit 3600
```

The original follower formulation can be run as

```bash
python main.py 20 20000 4 8 0.7 0 0 --timelimit 3600
```

The option `--degeneracy 1` requires `benders=1`.

For each run, the program generates the requested instance, solves the unblocked follower problem to determine the target coverage threshold, and then solves the selected algorithmic variant.

The main information reported for each run includes:

```text
Status
Solution time
Incumbent objective
Best bound
Final optimality gap
```

For the Benders-based method, additional statistics are reported, including the number of generated cuts, branch-and-bound nodes, and separation-time ratio.

## Input Instances

The computational instances are generated directly by `data/data.py`.

Each instance is characterized by the following main parameters:

* `n_facilities`: number of candidate facility locations;
* `n_demands`: number of customers;
* `coverage_radius`: radius of full coverage;
* `max_coverage_radius`: maximum covering radius;
* `decay_rate`: coverage decay parameter;
* `seed`: random seed.

For example,

```python
data.generate_random_instance(
    n_facilities=20,
    n_demands=5000,
    coverage_radius=4,
    max_coverage_radius=8,
    decay_rate=0.5,
    seed=0
)
```

generates an instance with 20 candidate facility locations and 5,000 customers.

For each generated instance, the data object contains the facility location and customer sets, facility costs, blocker costs, demand weights, coverage coefficients, facility budget, and covering-facility sets.

## Target Coverage Threshold

For each instance, the unblocked follower problem is solved first. Let its optimal objective value be denoted by (D0).

The target coverage threshold is then defined as

```text
t = beta * D0
```

where `beta` is the target coefficient used in the computational experiments.

The value of `beta` is supplied as a command-line argument to `main.py`.

## Output Format

Each computational run records the following information.

For the No-Benders method:

```text
status
incumbent objective
best bound
final optimality gap
solution time
```

For the Benders method:

```text
status
incumbent objective
best bound
final optimality gap
solution time
number of Benders cuts
number of branch-and-bound nodes
separation time / total solution time
```

The incumbent objective corresponds to the blocker cost of the best bilevel-feasible leader solution found during the solution process.

## Example Instance

An example test instance can be run directly from the command line. For example,

```bash
python main.py 20 20000 4 8 0.7 1 0 --degeneracy 0 --timelimit 3600
```

runs the standard Benders variant for an instance with 20 candidate facility locations, 20,000 customers, radii `(4, 8)`, target coefficient `beta=0.7`, and random seed `0`.

The corresponding output is:

```text
======================================================================
Instance: I=20, J=20000, seed=0
======================================================================
Coverage edges: 68936
Coverage density: 0.1723
Unblocked follower objective D0: 24194.94025055312
==================================================
Benders
==================================================
Status: Optimal
Time: 7.6191s
Incumbent objective: 9.0
Best bound: 9.0
Final gap: 0.0
Benders cuts: 3839
BB nodes: 418.0
Separation-time ratio: 0.3260
```

The reported solution time may vary slightly across machines and software configurations.

## License

This repository is provided for academic and research purposes.

## Citation

If you find this code useful in your research, please consider citing our paper:

```bibtex
@article{zhang2026mmclbp,
  title   = {An Exact Algorithm for the Max-Min Covering Location Blocker Problem},
  author  = {Zhang, Yun-Tian and Furini, Fabio and Ljubić, Ivana and Chen, Chen},
  journal = {arXiv preprint arXiv:XXXX.XXXXX},
  year    = {2026}
}
```
