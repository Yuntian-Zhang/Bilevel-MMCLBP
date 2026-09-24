"""Run OD+B&BC on the instances of the comparison with general-purpose solvers.

For every instance listed in instances/reference_optima.csv the script
regenerates the MMCLBP instance, sets the target t = 0.7 D0 exactly as
export_miblp.py does, and solves it with OD+B&BC (critical interdiction-cut
coefficients, follower solved by branch-and-Benders-cut) a given number of
times. It reports the optimum, the median running time and the number of outer
iterations, which are the OD+B&BC columns of Table 5 in the paper.

With --enumerate the optimum of the instances with at most ten facilities is
also recomputed by complete enumeration of the blocker decisions.
With --write the OD+B&BC columns of reference_optima.csv are overwritten.
"""

import argparse
import csv
import itertools
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0]))

from data.data import Data                                  # noqa: E402
from solver.bilevel_solver import BilevelSolver             # noqa: E402
from solver.sub_problem import SubProblemOri                # noqa: E402

TOL = 1e-6
CSV = HERE / "instances" / "reference_optima.csv"


def build(m, n, seed, beta):
    data = Data()
    data.generate_random_instance(m, n, 4, 8, 0.5, seed)
    _, _, d0 = SubProblemOri(data, None).solve()
    data.target_coverage = beta * d0
    return data


def enumerate_optimum(data):
    follower = SubProblemOri(data, None)
    best = None
    for bits in itertools.product((0, 1), repeat=len(data.I)):
        cost = sum(data.blocker_cost[i] * b for i, b in enumerate(bits))
        if best is not None and cost >= best:
            continue
        follower.update_x(dict(enumerate(bits)))
        _, _, value = follower.solve()
        if value <= data.target_coverage + TOL:
            best = cost
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--beta", type=float, default=0.7)
    ap.add_argument("--timelimit", type=float, default=600)
    ap.add_argument("--enumerate", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    with open(CSV, newline="") as fh:
        rows = list(csv.DictReader(fh))
    fields = list(rows[0])

    print(f"{'instance':<22}{'ref':>5}{'OD+B&BC':>9}{'enum':>6}"
          f"{'median s':>10}{'iters':>7}  check")
    failures = 0
    for r in rows:
        m, n, seed = int(r["m"]), int(r["n"]), int(r["seed"])
        data = build(m, n, seed, args.beta)
        times, iterations, objectives = [], [], []
        for _ in range(args.repeats):
            solver = BilevelSolver(data, {"Benders": 1, "Degeneracy": 0,
                                          "Coefficient": "critical",
                                          "TimeLimit": args.timelimit})
            result = solver.solve()
            if result["status"] != "Optimal":
                raise RuntimeError(f"{r['instance']}: status {result['status']}")
            times.append(result["time"])
            iterations.append(solver.subp_count)
            objectives.append(int(round(result["obj"])))
        obj = objectives[0]
        enum = enumerate_optimum(data) if args.enumerate and m <= 10 else None
        ok = (len(set(objectives)) == 1 and obj == int(r["optimum"])
              and (enum is None or enum == obj)
              and abs(data.target_coverage - float(r["t"])) < 1e-5)
        failures += not ok
        print(f"{r['instance']:<22}{r['optimum']:>5}{obj:>9}"
              f"{enum if enum is not None else '-':>6}"
              f"{statistics.median(times):>10.3f}{iterations[0]:>7}  "
              f"{'ok' if ok else 'MISMATCH'}")
        r["od_bbc_median_s"] = f"{statistics.median(times):.3f}"
        r["od_bbc_iterations"] = str(iterations[0])

    if args.write:
        with open(CSV, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(f"updated {CSV.name}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
