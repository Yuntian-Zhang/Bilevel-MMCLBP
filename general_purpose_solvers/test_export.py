"""Validate the MibS export of every small MMCLBP instance.

For each instance and for EVERY one of the 2^m leader decisions, the follower
of the exported .mps is solved and compared with the repository follower.
The bilevel optimum is then recovered from the export by enumeration and
compared with the reference optimum and with OD+B&BC.
Also reported: the high-point-relaxation bound the general-purpose solver
would start from.
"""

import csv
import itertools
import math
import sys
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0]))

from data.data import Data                                  # noqa: E402
from solver.sub_problem import SubProblemOri                # noqa: E402
from solver.bilevel_solver import BilevelSolver             # noqa: E402

TOL = 1e-6


def read_aux(path):
    lc, lr, lo, os_ = [], [], [], None
    for line in path.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "LC":
            lc.append(int(parts[1]))
        elif parts[0] == "LR":
            lr.append(int(parts[1]))
        elif parts[0] == "LO":
            lo.append(float(parts[1]))
        elif parts[0] == "OS":
            os_ = int(parts[1])
    return lc, lr, lo, os_


def check(rec):
    name, m, n, seed = rec["instance"], int(rec["m"]), int(rec["n"]), int(rec["seed"])
    ref_opt, ref_t = int(rec["optimum"]), float(rec["t"])
    mps = HERE / "instances" / f"{name}.mps"

    data = Data()
    data.generate_random_instance(m, n, 4, 8, 0.5, seed)
    _, _, d0 = SubProblemOri(data, None).solve()
    data.target_coverage = 0.7 * d0
    assert abs(data.target_coverage - ref_t) < 1e-6, "target mismatch"  # csv is rounded

    model = gp.read(str(mps))
    model.Params.OutputFlag = 0
    col = {v.VarName: v for v in model.getVars()}
    order = [v.VarName for v in model.getVars()]
    rows = [c.ConstrName for c in model.getConstrs()]

    # 1. the .aux indices must select exactly the y/r columns and the non-coupling rows
    lc, lr, lo, os_ = read_aux(HERE / "instances" / f"{name}.aux")
    aux_ok = (
        [order[k] for k in lc] == [v for v in order if v[0] in "yr"]
        and [rows[k] for k in lr] == [r for r in rows if r != "cover"]
        and os_ == -1
        and all(abs(lo[k] - (0.0 if order[i][0] == "y" else float(data.demand_weight[int(order[i][1:])]))) < 1e-12
                for k, i in enumerate(lc))
    )
    # 2. high-point relaxation, the bound a general-purpose MIBLP solver starts from
    model.optimize()
    hpr = model.ObjVal

    # 3. follower of the exported model vs repository follower, over ALL leader decisions
    model.remove(model.getConstrByName("cover"))
    model.update()
    model.setObjective(
        gp.quicksum(float(data.demand_weight[j]) * col[f"r{j}"] for j in range(n)),
        GRB.MAXIMIZE,
    )
    follower = SubProblemOri(data, None)
    max_dev = 0.0
    best = math.inf
    for bits in itertools.product((0, 1), repeat=m):
        for i, b in enumerate(bits):
            col[f"x{i}"].LB = col[f"x{i}"].UB = b
        model.optimize()
        exported = model.ObjVal
        follower.update_x(dict(enumerate(bits)))
        _, _, repo = follower.solve()
        max_dev = max(max_dev, abs(exported - repo))
        if exported <= data.target_coverage + TOL:
            best = min(best, sum(bits))

    # 4. OD+B&BC on the same instance
    alg = BilevelSolver(data, {"Benders": 1, "Degeneracy": 0, "TimeLimit": 300}).solve()

    model.dispose()
    return {
        "instance": name, "m": m, "n": n,
        "ll_vars": len(lc), "ll_rows": len(lr),
        "aux_ok": aux_ok,
        "hpr": hpr, "max_dev": max_dev,
        "opt_export": best, "opt_ref": ref_opt, "opt_alg": alg["obj"],
        "ok": aux_ok and max_dev < 1e-9
              and best == ref_opt == int(round(alg["obj"])),
    }


def main():
    with open(HERE / "instances" / "validation_optima.csv") as f:
        recs = list(csv.DictReader(f))
    results = [check(r) for r in recs]

    print(f"\n{'instance':<20}{'LLv':>5}{'LLr':>6}{'aux':>5}{'HPR':>6}"
          f"{'max dev':>11}{'export':>8}{'enum':>6}{'alg':>5}{'':>4}")
    print("-" * 76)
    for r in results:
        print(f"{r['instance']:<20}{r['ll_vars']:>5}{r['ll_rows']:>6}"
              f"{'ok' if r['aux_ok'] else 'BAD':>5}"
              f"{r['hpr']:>6.1f}{r['max_dev']:>11.2e}"
              f"{r['opt_export']:>8}{r['opt_ref']:>6}{r['opt_alg']:>5.0f}"
              f"{'  ok' if r['ok'] else '  FAIL':>4}")
    bad = [r for r in results if not r["ok"]]
    print("-" * 76)
    print(f"{len(results) - len(bad)}/{len(results)} instances passed; "
          f"worst follower deviation {max(r['max_dev'] for r in results):.2e}; "
          f"HPR bound is {max(r['hpr'] for r in results):.0f} on every instance")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
