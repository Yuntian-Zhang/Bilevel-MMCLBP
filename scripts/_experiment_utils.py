"""Shared utilities for reproducible computational experiments."""

import csv
from datetime import datetime, timezone
from pathlib import Path

from data.data import Data
from solver.bilevel_solver import BilevelSolver
from solver.sub_problem import SubProblem, SubProblemOri


ROOT = Path(__file__).resolve().parents[1]
GENERATED_RESULTS = ROOT / "results" / "generated"


def reset_benders_statistics():
    callback = SubProblem.benders_callback
    callback.initialized = True
    callback.integer_cuts = 0
    callback.fractional_cuts = 0
    callback.bb_nodes = 0
    callback.integer_time = 0.0
    callback.fractional_time = 0.0


def set_target_from_unblocked_follower(data, beta: float, use_benders: bool = False):
    """Solve the unblocked follower and set the target used by the leader."""
    follower = SubProblem(data, None, {"Degeneracy": 0}) if use_benders else SubProblemOri(data, None)
    _, _, d0 = follower.solve()
    if d0 is None:
        raise RuntimeError(f"Unblocked follower did not solve to optimality (status {follower.status}).")
    data.target_coverage = beta * d0
    return d0


def run_synthetic_instance(
    n_facilities,
    n_demands,
    r1,
    r2,
    beta,
    benders,
    seed,
    time_limit,
    coefficient="critical",
):
    data = Data()
    data.generate_random_instance(
        n_facilities=n_facilities,
        n_demands=n_demands,
        coverage_radius=r1,
        max_coverage_radius=r2,
        decay_rate=0.5,
        seed=seed,
    )
    d0 = set_target_from_unblocked_follower(data, beta, use_benders=True)
    reset_benders_statistics()
    parameters = {
        "Benders": 1 if benders else None,
        "Degeneracy": 0,
        "Coefficient": coefficient,
        "TimeLimit": time_limit,
    }
    result = BilevelSolver(data, parameters).solve()
    return {
        "facilities": n_facilities,
        "demands": n_demands,
        "r1": r1,
        "r2": r2,
        "beta": beta,
        "seed": seed,
        "method": "benders" if benders else "milp",
        "coefficient": coefficient,
        "unblocked_objective": d0,
        "target_coverage": data.target_coverage,
        "status": result["status"],
        "objective": result["obj"],
        "bound": result["bound"],
        "gap": result["gap"],
        "time_seconds": result["time"],
        "benders_cuts": getattr(SubProblem.benders_callback, "integer_cuts", 0) if benders else 0,
        "max_bb_nodes": getattr(SubProblem.benders_callback, "bb_nodes", 0) if benders else 0,
    }


def write_rows(rows, prefix: str):
    """Write result dictionaries to a timestamped CSV file."""
    if not rows:
        raise ValueError("No result rows to write.")
    GENERATED_RESULTS.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = GENERATED_RESULTS / f"{prefix}_{timestamp}.csv"
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return output
