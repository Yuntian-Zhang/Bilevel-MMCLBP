"""Reproduce the Virginia Beach case study of the paper."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.virginia_beach import load_virginia_beach_instance
from solver.bilevel_solver import BilevelSolver
from _experiment_utils import reset_benders_statistics, set_target_from_unblocked_follower, write_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=ROOT / "data" / "virginia_beach" / "VBOHCAR.xlsx",
        help="Path to the Virginia Beach workbook.",
    )
    parser.add_argument("--timelimit", type=float, default=3600.0)
    parser.add_argument("--beta", type=float, default=0.7)
    parser.add_argument("--skip-reference-check", action="store_true")
    args = parser.parse_args()

    data = load_virginia_beach_instance(args.data)
    d0 = set_target_from_unblocked_follower(data, args.beta, use_benders=True)
    if not args.skip_reference_check and abs(d0 - 1775.42) > 0.05:
        raise AssertionError(
            f"Unexpected unblocked value {d0:.4f}; expected approximately 1775.42."
        )

    reset_benders_statistics()
    result = BilevelSolver(
        data,
        {"Benders": 1, "Degeneracy": 0, "TimeLimit": args.timelimit},
    ).solve()
    row = {
        "facilities": len(data.I),
        "demands": len(data.J),
        "coverage_radius_km": data.coverage_radius,
        "max_coverage_radius_km": data.max_coverage_radius,
        "decay_rate": data.decay_rate,
        "facility_budget": data.facility_budget,
        "beta": args.beta,
        "unblocked_objective": d0,
        "target_coverage": data.target_coverage,
        "status": result["status"],
        "objective": result["obj"],
        "bound": result["bound"],
        "gap": result["gap"],
        "time_seconds": result["time"],
    }
    output = write_rows([row], "virginia_beach")
    print(f"Unblocked follower objective: {d0:.4f}")
    print(f"Target coverage: {data.target_coverage:.4f}")
    print(f"Status: {result['status']}")
    print(f"Blocker objective: {result['obj']}")
    print(f"Wrote result to {output}")


if __name__ == "__main__":
    main()
