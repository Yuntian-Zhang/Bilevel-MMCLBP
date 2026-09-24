"""Regenerate the interdiction-cut coefficient ablation experiment."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _experiment_utils import run_synthetic_instance, write_rows


DIAGNOSTIC_GRID = ((20, 20000), (25, 20000), (35, 10000))
COEFFICIENTS = ("global", "nogood", "critical")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timelimit", type=float, default=3600.0)
    parser.add_argument("--quick", action="store_true", help="Run only the 20-by-20,000 class.")
    args = parser.parse_args()

    rows = []
    grid = DIAGNOSTIC_GRID[:1] if args.quick else DIAGNOSTIC_GRID
    for n_facilities, n_demands in grid:
        for coefficient in COEFFICIENTS:
            for seed in range(3):
                row = run_synthetic_instance(
                    n_facilities,
                    n_demands,
                    4,
                    8,
                    0.7,
                    True,
                    seed,
                    args.timelimit,
                    coefficient=coefficient,
                )
                rows.append(row)
                print(
                    f"{coefficient} I={n_facilities} J={n_demands} seed={seed}: "
                    f"{row['status']} obj={row['objective']} time={row['time_seconds']:.2f}s"
                )

    output = write_rows(rows, "coefficient_ablation")
    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
