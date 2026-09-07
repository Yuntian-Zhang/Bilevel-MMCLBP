"""Regenerate raw results for the main synthetic benchmark."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _experiment_utils import run_synthetic_instance, write_rows


FULL_GRID = [(20, 5000), (20, 10000), (20, 20000), (20, 30000), (20, 50000),
             (25, 5000), (25, 10000), (25, 20000), (25, 30000), (25, 50000),
             (35, 5000), (35, 10000), (35, 20000)]
QUICK_GRID = [(20, 20000), (25, 20000)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="Run all 65 benchmark instances per selected method.")
    parser.add_argument("--quick", action="store_true", help="Run the compact default benchmark explicitly.")
    parser.add_argument("--method", choices=("benders", "milp", "both"), default="both")
    parser.add_argument("--timelimit", type=float, default=3600.0)
    args = parser.parse_args()

    if args.full and args.quick:
        parser.error("Choose at most one of --full and --quick.")

    grid = FULL_GRID if args.full else QUICK_GRID
    seeds = range(5) if args.full else range(3)
    methods = (True, False) if args.method == "both" else (args.method == "benders",)
    rows = []

    for use_benders in methods:
        for n_facilities, n_demands in grid:
            for seed in seeds:
                row = run_synthetic_instance(
                    n_facilities, n_demands, 4, 8, 0.7, use_benders, seed, args.timelimit
                )
                rows.append(row)
                print(
                    f"{row['method']} I={n_facilities} J={n_demands} seed={seed}: "
                    f"{row['status']} obj={row['objective']} time={row['time_seconds']:.2f}s"
                )

    output = write_rows(rows, "main_benchmark")
    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
