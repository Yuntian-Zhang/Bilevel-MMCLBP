"""Assemble the appendix comparison table from the raw solver run logs.

Reads:
  runs/hcpp.txt                   output of  run_hcpp.sh 99  (HC++)
  runs/mibs.txt                   output of  run_mibs.sh
  instances/reference_optima.csv  optima, OD+B&BC median times and outer
                                  iterations (written by run_od_bbc.py)

Writes the LaTeX tabular of Table 5 of the paper to stdout.  Cells with no run are printed as "--".
"""

import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TL = 600.0

# factorial grid: |I| x |J|, one instance per cell
GRID = [(m, n) for m in (10, 15, 20) for n in (50, 500, 5000)]


def key(name):
    """(m, n) for seed-0 instances only; the ladder is defined on seed 0."""
    m = re.search(r"_m(\d+)_n(\d+)_s0$", name)
    return (int(m.group(1)), int(m.group(2))) if m else None


def read_hcpp(path):
    """name -> (time, status) with status in {opt, tl_inc, tl_none, wrong}."""
    res = {}
    for line in Path(path).read_text().splitlines():
        f = line.split()
        if len(f) < 7 or not f[0].startswith(("mmclbp_", "zform_")):
            continue
        k = key(f[0])
        # columns: name ref zbest root_bnd time nodes opt status...
        ref, z, t, op = int(f[1]), float(f[2]), float(f[4]), f[6]
        if k is None:
            continue
        nodes = f[5]
        if op == "1":
            st = "opt" if abs(z - ref) < 0.5 else "wrong"
        elif z > 1e18:
            st = "tl_none"
        else:
            st = "tl_inc"
        res[k] = (t, st, z, ref, nodes)
    return res


def read_mibs(path):
    res = {}
    for line in Path(path).read_text().splitlines():
        f = line.split()
        if len(f) < 5 or not f[0].startswith("mmclbp_"):
            continue
        k = key(f[0])
        if k is None:
            continue
        t = float(f[3])
        st = "opt" if f[4] == "match" else ("tl_none" if f[4] in ("fail", "timeout") else "wrong")
        res[k] = (t, st, f[2], int(f[1]), f[7])   # f[7] = branch-and-bound nodes
    return res


def read_od_bbc(path):
    """(median time, optimum, outer iterations) per size."""
    res = {}
    with open(path) as fh:
        for r in csv.DictReader(fh):
            res[(int(r["m"]), int(r["n"]))] = (float(r["od_bbc_median_s"]),
                                              int(r["optimum"]),
                                              int(r["od_bbc_iterations"]))
    return res


def cell(entry):
    if entry is None:
        return "--", None
    t, st = entry[0], entry[1]
    if st == "opt":
        return f"{t:.2f}", t
    if st in ("tl_inc", "tl_none"):
        return "TL", None
    return f"\\textbf{{wrong}}", None


def main():
    runs = HERE / "runs"
    hcpp = read_hcpp(runs / "hcpp.txt") if (runs / "hcpp.txt").exists() else {}
    mibs = read_mibs(runs / "mibs.txt") if (runs / "mibs.txt").exists() else {}
    od_bbc = read_od_bbc(HERE / "instances" / "reference_optima.csv")

    print(r"\begin{tabular}{rrr rrr rr rrr}")
    print(r"\toprule")
    print(r"& & & \multicolumn{3}{c}{Time (s)} "
          r"& \multicolumn{2}{c}{Slowdown factor} "
          r"& \multicolumn{3}{c}{Search effort} \\")
    print(r"\cmidrule(lr){4-6}\cmidrule(lr){7-8}\cmidrule(lr){9-11}")
    print(r"$|I|$ & $|J|$ & obj. & \texttt{OD+B\&BC} & HC++ & MibS "
          r"& HC++ & MibS & \texttt{OD+B\&BC} & HC++ & MibS \\")
    print(r"\midrule")
    for m, n in GRID:
        o = od_bbc.get((m, n))
        if o is None:
            continue
        ot, z, oi = o
        fc, ft = cell(hcpp.get((m, n)))
        mc, mt = cell(mibs.get((m, n)))
        rf = f"{ft / ot:,.0f}" if ft else "--"
        rm = f"{mt / ot:,.0f}" if mt else "--"
        fe = hcpp.get((m, n))
        me = mibs.get((m, n))
        # search effort is meaningful only where optimality was proven: at the
        # time limit it measures the work done in 600 s, not the work required
        en = (f"{int(fe[4]):,}" if fe and fe[1] == "opt" and fe[4].isdigit() else "--")
        ev = (f"{int(me[4]):,}" if me and me[1] == "opt" and me[4].isdigit() else "--")
        print(f"{m} & {n:,} & {z} & {ot:.2f} & {fc} & {mc} & {rf} & {rm} "
              f"& {oi:,} & {en} & {ev} \\\\")
    print(r"\bottomrule")
    print(r"\end{tabular}")


if __name__ == "__main__":
    sys.exit(main())
