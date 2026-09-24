# Comparison with general-purpose bilevel solvers

This page explains how to reproduce Appendix A of the paper (Table 5), where
`OD+B&BC` is compared with two general-purpose solvers for mixed-integer
bilevel linear programs:

- **HC++**, the hypercube setting of the branch-and-cut solver of Fischetti,
  Ljubić, Monaci and Sinnl (*A new general-purpose algorithm for mixed-integer
  bilevel linear programs*, Operations Research 2017; *On the use of
  intersection cuts for bilevel optimization*, Mathematical Programming 2018);
- **MibS** 1.2.2, the open-source solver of Tahernejad, Ralphs and DeNegre
  (*A branch-and-cut algorithm for mixed integer bilevel linear optimization
  problems and its implementation*, Mathematical Programming Computation 2020).

Neither solver is distributed with this repository. Everything needed to
produce their input files, run them, and build the table is in
`general_purpose_solvers/`.

## Formulation passed to the solvers

Replacing the definition of the coverage `r_j` in the follower problem by the
two families of linear constraints of Section 2.2 gives a bilevel program with
linear constraints at both levels:

```text
upper level   min  sum_i e_i x_i
              s.t. sum_j d_j r_j <= t                     (target coverage)
                   x in {0,1}^m

lower level   max  sum_j d_j r_j
              s.t. r_j + (1 - p_ij) y_i <= 1              j in J, i in I_j
                   r_j - sum_{i in I_j} p_ij y_i <= 0     j in J
                   sum_i f_i y_i <= b
                   y_i + x_i <= 1                         i in I
                   y in {0,1}^m,  r in [0,1]^n
```

The follower optimizes without the target-coverage row. Since that row depends
only on the follower value, the optimistic and pessimistic conventions
coincide.

Each instance is written in the MibS input format, read by both solvers: an
`.mps` file with the high-point relaxation and an `.aux` file declaring the
lower-level columns (`LC`), rows (`LR`), objective (`LO`) and sense (`OS -1`,
maximization). Columns are written in the order `x`, `y`, `r`, and rows in the
order target coverage, first family, second family, budget, linking, so that
the zero-based indices of the `.aux` file are unambiguous.

Only the hypercube settings of the first solver apply to the MMCLBP. The
intersection-cut and XU settings require a follower with integer variables and
integer coefficients, whereas the coverage variables `r` are continuous and the
coefficients `p_ij` and `1 - p_ij` are fractional.

## Instances

`general_purpose_solvers/instances/` contains:

| Files | Content |
| --- | --- |
| `mmclbp_m{10,15,20}_n{50,500,5000}_s0.{mps,aux}` | the nine instances of Table 5 |
| `valid_m{5,6,7,8,10}_n{20,25,30,40,50}_s{0,1,2}.{mps,aux}` | fifteen small validation instances |
| `reference_optima.csv` | for the nine instances: `D0`, target `t`, budget `b`, optimum, its source (`enum` for complete enumeration, `alg` for `OD+B&BC`), median `OD+B&BC` time and outer iterations |
| `validation_optima.csv` | `D0`, `t` and optimum of the validation instances |

The instances are generated as in Section 5.1 of the paper, with seed `s`, unit
costs, budget `b = floor(0.2 |I|)` and target `t = 0.7 D0`. They can be
regenerated with

```bash
cd general_purpose_solvers
python3 export_miblp.py --facilities 10 --customers 500 --seed 0
python3 export_miblp.py --facilities 5 --customers 20 --seed 1 --prefix valid
```

The regenerated files are identical to the ones in `instances/`.

## Obtaining the solvers

**HC++.** The binary is distributed by its authors at
<https://msinnl.github.io/pages/bilevel.html>. It requires a license file,
which is requested from the authors, and IBM ILOG CPLEX. Build the CPLEX
dynamic libraries as described in the readme that comes with the binary, and
place the binary, the libraries and the license file in one directory. The
binary uses only the CPLEX callable C library, so dynamic libraries built from
a CPLEX version more recent than the one it was compiled with also work.

**MibS.** Version 1.2.2 is available from COIN-OR at
<https://github.com/coin-or/MibS> and is built with `coinbrew`, following the
instructions of that repository.

## Running the comparison

All commands are run from `general_purpose_solvers/`, after installing this
package as described in [Installation](installation.md).

```bash
# 1. check the encoding (optional)
python3 test_export.py

# 2. OD+B&BC: optima, median time over three runs, outer iterations
python3 run_od_bbc.py              # add --write to update reference_optima.csv

# 3. the two general-purpose solvers, 600 s each
HCPP_DIR=/path/to/solver ./run_hcpp.sh 99 600 'mmclbp_m*_s0' | tail -n +3 > runs/hcpp.txt
MIBS_DIR=/path/to/mibs/dist ./run_mibs.sh 600 'mmclbp_m*_s0' | tail -n +3 > runs/mibs.txt
# or both at once, N jobs in parallel:
HCPP_DIR=/path/to/solver MIBS_DIR=/path/to/mibs/dist ./run_all.sh N 600

# 4. Table 5
python3 make_comparison_table.py
```

`test_export.py` checks, for every validation instance, that the `.aux` indices
select exactly the lower-level columns and rows, solves the follower of the
exported program for every blocker decision and compares it with the follower
of this package, and recovers the optimum by complete enumeration.

`run_hcpp.sh` and `run_mibs.sh` compare each result with the reference optimum
and report `opt`/`match`, a time-limit status, or a mismatch. Running them on
the pattern `'valid_*'` checks both solvers on the validation instances.

## Configuration used in the paper

- HC++: setting `99`, `-num_threads 1 -randomseed -1` (single thread,
  deterministic), `-time_limit 600`.
- MibS 1.2.2: default parameters, serial, `-Alps_timeLimit 600`.
- `OD+B&BC`: critical interdiction-cut coefficients and the
  branch-and-Benders-cut follower; the time reported is the median of three
  runs.

The hardware is described in Appendix A of the paper.

## Raw results

`general_purpose_solvers/runs/` contains the solver outputs behind Table 5:

| File | Content |
| --- | --- |
| `hcpp.txt`, `mibs.txt` | the nine instances of Table 5 |
| `hcpp_validation.txt`, `mibs_validation.txt` | the fifteen validation instances |

Columns of `hcpp.txt`: instance, reference optimum, best objective, root bound,
time (s), branch-and-bound nodes, optimality flag (`1` proven, `0` time limit),
status. Columns of `mibs.txt`: instance, reference optimum, objective, time
(s), status, value-function problems solved, cuts, branch-and-bound nodes.
