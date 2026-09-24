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
| `benders` | `0` or `1` | Direct MILP follower or closed-form Benders follower |
| `seed` | integer | Random-instance seed |

Optional inputs:

| Option | Default | Meaning |
| --- | --- | --- |
| `--coefficient` | `critical` | Interdiction-cut coefficient of the outer decomposition: `global`, `nogood`, or `critical` |
| `--degeneracy` | `0` | Add the alternative dual-degeneracy cut when using Benders |
| `--timelimit` | `3600` | Global wall-clock limit in seconds |

The program prints the coverage-edge count, unblocked follower value `D0`,
target `beta * D0`, solution status, incumbent objective, bound, gap, elapsed
time, and (for Benders) generated-cut and branch-and-bound statistics.

## Reproduction-script outputs

The scripts in `scripts/` write timestamped CSV files to `results/generated/`.
The synthetic-result schema is:

| Field | Meaning |
| --- | --- |
| `facilities`, `demands`, `r1`, `r2`, `beta`, `seed` | Complete instance specification |
| `method`, `coefficient` | Follower and outer-cut configuration |
| `unblocked_objective`, `target_coverage` | Value used to define the blocker target |
| `status` | `Optimal`, `TimeLimit`, or a reported solver status |
| `objective`, `bound`, `gap`, `time_seconds` | Final outer-algorithm result |
| `benders_cuts`, `max_bb_nodes` | Benders diagnostics; zero for the direct MILP follower |

The Virginia Beach script writes the same solution fields together with its
coverage parameters and follower budget. A `TimeLimit` row contains the best
checked incumbent and bound available when the global time limit expires; it
must not be treated as a proven optimum.
