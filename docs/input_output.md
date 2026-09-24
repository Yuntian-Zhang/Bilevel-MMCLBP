# Inputs and outputs

## Single synthetic instance

```bash
python3 main.py I J r1 r2 beta benders seed [options]
```

| Input | Type | Meaning |
| --- | --- | --- |
| `I` | integer | Number of candidate facilities |
| `J` | integer | Number of demand points |
| `r1` | float | Full-coverage radius |
| `r2` | float | Maximum-coverage radius; must be at least `r1` |
| `beta` | float | Target fraction of the unblocked follower value |
| `benders` | `0` or `1` | `0`: `OD+MILP`, follower solved as an MILP; `1`: `OD+B&BC`, follower solved by branch-and-Benders-cut with closed-form separation |
| `seed` | integer | Random-instance seed |

Optional inputs:

| Option | Default | Meaning |
| --- | --- | --- |
| `--coefficient` | `critical` | Interdiction-cut coefficients: `critical` (Proposition 2 of the paper), `nogood` (the no-good interdiction cuts of Section 3.2), or `global` (uniform coefficient equal to the sum of the demand weights; not reported in the paper) |
| `--degeneracy` | `0` | Add the alternative dual-degeneracy Benders cut (Section EC.5.1); requires `benders=1` |
| `--timelimit` | `3600` | Global wall-clock limit in seconds |

The program prints the coverage-edge count, unblocked follower value `D0`,
target `beta * D0`, solution status, incumbent objective, bound, gap, elapsed
time, and (for `OD+B&BC`) the number of Benders cuts and branch-and-bound statistics.

## Reproduction-script outputs

The scripts in `scripts/` write timestamped CSV files to `results/generated/`.
The synthetic-result schema is:

| Field | Meaning |
| --- | --- |
| `facilities`, `demands`, `r1`, `r2`, `beta`, `seed` | Complete instance specification |
| `method`, `coefficient` | `benders` (`OD+B&BC`) or `milp` (`OD+MILP`), and interdiction-cut coefficients |
| `unblocked_objective`, `target_coverage` | Value used to define the blocker target |
| `status` | `Optimal`, `TimeLimit`, or a reported solver status |
| `objective`, `bound`, `gap`, `time_seconds` | Final result of the outer decomposition |
| `benders_cuts`, `max_bb_nodes` | Benders cuts and maximum branch-and-bound nodes in any single follower solve; zero for `OD+MILP` |

The Virginia Beach script writes the same solution fields together with its
coverage parameters and follower budget. A `TimeLimit` row contains the best
checked incumbent and bound available when the global time limit expires; it
must not be treated as a proven optimum.
