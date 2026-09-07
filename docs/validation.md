# Validation

Run the automated checks after installation:

```bash
make test
make smoke
```

The `pytest` suite checks that the Benders follower equals the direct MILP
follower for every blocker configuration of a small instance, and that the
outer Benders algorithm matches complete blocker enumeration. `make smoke`
extends this comparison to three small random instances.

The validation machine used Python 3.10, Gurobi 13.0.3, NumPy 2.2.6, and
pybind11 3.1.0. It reproduced the following blocker objectives:

| Facilities | Demands | Seeds 0, 1, 2 |
| ---: | ---: | --- |
| 20 | 20,000 | 9, 5, 7 |
| 25 | 20,000 | 9, 7, 9 |

The results confirm optimal objectives. Running times and internal cut counts
can differ with processor, operating system, Gurobi version, and thread
scheduling.
