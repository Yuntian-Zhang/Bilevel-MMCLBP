"""Export an MMCLBP instance as a mixed-integer bilevel linear program in the
MibS input format (.mps + .aux). The same format is read by MibS and by the
general-purpose bilevel solver of Fischetti, Ljubic, Monaci and Sinnl, whose
hypercube setting HC++ is used in Appendix A of the paper.

MIBLP encoding
--------------
upper level   min  sum_i e_i x_i
              s.t. sum_j d_j r_j <= t                      (UL coupling row)

lower level   max  sum_j d_j r_j
              s.t. r_j + (1-p_ij) y_i <= 1   j in J, i in I_j
                   r_j - sum_{i in I_j} p_ij y_i <= 0   j in J
                   sum_i f_i y_i <= b
                   y_i + x_i <= 1            i in I
                   y in {0,1}^m,  r in [0,1]^n

Columns are emitted in the order x, y, r and rows in the order
coupling, LL1, LL2, budget, linking, so that the zero-based indices used by
the legacy .aux format are unambiguous.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.data import Data                      # noqa: E402
from solver.sub_problem import SubProblemOri     # noqa: E402


def build(data):
    """Return (columns, rows) describing the MIBLP.

    columns: list of (name, kind, lower, upper, obj_ul, obj_ll)
    rows:    list of (name, level, [(col_name, coef)], sense, rhs)
    """
    m, n = len(data.I), len(data.J)
    d = np.asarray(data.demand_weight, dtype=float)
    p = data.prob

    cols = []
    for i in range(m):
        cols.append((f"x{i}", "B", 0.0, 1.0, float(data.blocker_cost[i]), 0.0))
    for i in range(m):
        cols.append((f"y{i}", "B", 0.0, 1.0, 0.0, 0.0))
    for j in range(n):
        cols.append((f"r{j}", "C", 0.0, 1.0, 0.0, float(d[j])))

    rows = []
    # upper-level coupling row: sum_j d_j r_j <= t
    rows.append(("cover", "UL",
                 [(f"r{j}", float(d[j])) for j in range(n) if d[j] != 0.0],
                 "L", float(data.target_coverage)))
    # LL1: r_j + (1-p_ij) y_i <= 1
    for j in range(n):
        for i in data.covering_facilities[j]:
            rows.append((f"c1_{j}_{i}", "LL",
                         [(f"r{j}", 1.0), (f"y{int(i)}", 1.0 - float(p[i, j]))],
                         "L", 1.0))
    # LL2: r_j - sum_{i in I_j} p_ij y_i <= 0
    for j in range(n):
        terms = [(f"r{j}", 1.0)]
        terms += [(f"y{int(i)}", -float(p[i, j])) for i in data.covering_facilities[j]]
        rows.append((f"c2_{j}", "LL", terms, "L", 0.0))
    # budget
    rows.append(("budget", "LL",
                 [(f"y{i}", float(data.facility_cost[i])) for i in range(m)],
                 "L", float(data.facility_budget)))
    # linking: y_i + x_i <= 1
    for i in range(m):
        rows.append((f"link{i}", "LL", [(f"y{i}", 1.0), (f"x{i}", 1.0)], "L", 1.0))

    return cols, rows


def num(v):
    """Full-precision decimal literal; never a numpy repr."""
    return repr(float(v))


def write_mps(path, name, cols, rows):
    col_terms = {c[0]: [] for c in cols}
    for rname, _lvl, terms, _sense, _rhs in rows:
        for cname, coef in terms:
            col_terms[cname].append((rname, coef))

    with open(path, "w") as f:
        f.write(f"NAME{' ' * 10}{name}\n")
        f.write("ROWS\n")
        f.write(" N  obj\n")
        for rname, _lvl, _terms, sense, _rhs in rows:
            f.write(f" {sense}  {rname}\n")
        f.write("COLUMNS\n")
        integer_open = False
        for cname, kind, _lo, _up, obj_ul, _obj_ll in cols:
            want_int = kind == "B"
            if want_int != integer_open:
                marker = "INTORG" if want_int else "INTEND"
                f.write(f"    MARKER{' ' * 16}'MARKER'{' ' * 17}'{marker}'\n")
                integer_open = want_int
            entries = ([("obj", obj_ul)] if obj_ul != 0.0 else []) + col_terms[cname]
            if not entries:
                entries = [("obj", 0.0)]
            for k in range(0, len(entries), 2):
                chunk = entries[k:k + 2]
                line = f"    {cname:<10}"
                for rname, coef in chunk:
                    line += f"  {rname:<10}  {num(coef):<24}"
                f.write(line.rstrip() + "\n")
        if integer_open:
            f.write(f"    MARKER{' ' * 16}'MARKER'{' ' * 17}'INTEND'\n")
        f.write("RHS\n")
        for rname, _lvl, _terms, _sense, rhs in rows:
            if rhs != 0.0:
                f.write(f"    rhs         {rname:<10}  {num(rhs)}\n")
        f.write("BOUNDS\n")
        for cname, kind, lo, up, _o1, _o2 in cols:
            if kind == "B":
                f.write(f" BV bnd       {cname}\n")
            else:
                f.write(f" UP bnd       {cname:<10}  {num(up)}\n")
                if lo != 0.0:
                    f.write(f" LO bnd       {cname:<10}  {num(lo)}\n")
        f.write("ENDATA\n")


def write_aux(path, cols, rows, mps_name, sense):
    """Legacy index-based .aux. sense='max' -> OS -1 with +d; 'min' -> OS 1 with -d."""
    ll_cols = [(k, c) for k, c in enumerate(cols) if c[0][0] != "x"]
    ll_rows = [k for k, r in enumerate(rows) if r[1] == "LL"]
    sign = 1.0 if sense == "max" else -1.0
    with open(path, "w") as f:
        f.write(f"N {len(ll_cols)}\n")
        f.write(f"M {len(ll_rows)}\n")
        for k, _c in ll_cols:
            f.write(f"LC {k}\n")
        for k in ll_rows:
            f.write(f"LR {k}\n")
        for _k, c in ll_cols:
            f.write(f"LO {num(sign * c[5])}\n")
        f.write(f"OS {-1 if sense == 'max' else 1}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facilities", type=int, default=6)
    ap.add_argument("--customers", type=int, default=25)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--beta", type=float, default=0.7)
    ap.add_argument("--outdir", default=str(Path(__file__).resolve().parent / "instances"))
    ap.add_argument("--prefix", default="mmclbp",
                    help="file-name prefix; the validation instances use 'valid'")
    args = ap.parse_args()

    data = Data()
    data.generate_random_instance(args.facilities, args.customers, 4, 8, 0.5, args.seed)
    _, _, d0 = SubProblemOri(data, None).solve()
    data.target_coverage = args.beta * d0

    cols, rows = build(data)
    stem = f"{args.prefix}_m{args.facilities}_n{args.customers}_s{args.seed}"
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    write_mps(out / f"{stem}.mps", stem, cols, rows)
    write_aux(out / f"{stem}.aux", cols, rows, f"{stem}.mps", "max")

    print(f"unblocked follower optimum D0 = {d0:.6f}")
    print(f"target coverage t = {data.target_coverage:.6f}")
    print(f"columns {len(cols)}  rows {len(rows)}  "
          f"LL vars {sum(1 for c in cols if c[0][0] != 'x')}  "
          f"LL rows {sum(1 for r in rows if r[1] == 'LL')}")
    print(f"written to {out}/{stem}.[mps|aux]")


if __name__ == "__main__":
    main()
