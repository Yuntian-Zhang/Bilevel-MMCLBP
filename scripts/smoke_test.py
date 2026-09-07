"""Run a quick exactness check of the two follower implementations."""

import itertools
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.data import Data
from solver.bilevel_solver import BilevelSolver
from solver.sub_problem import SubProblem, SubProblemOri


def check_case(n_facilities, n_demands, seed):
    data = Data()
    data.generate_random_instance(n_facilities, n_demands, 4, 8, 0.5, seed)
    unblocked = SubProblemOri(data, None)
    _, _, d0 = unblocked.solve()
    if d0 is None:
        raise RuntimeError("Could not solve the unblocked follower.")
    data.target_coverage = 0.7 * d0

    milp_follower = SubProblemOri(data, None)
    benders_follower = SubProblem(data, None, {"Degeneracy": 0})
    brute_force_objective = math.inf
    maximum_difference = 0.0

    for bits in itertools.product((0, 1), repeat=n_facilities):
        x = dict(enumerate(bits))
        milp_follower.update_x(x)
        _, _, milp_value = milp_follower.solve()
        benders_follower.update_x(x)
        _, _, benders_value = benders_follower.solve()
        maximum_difference = max(maximum_difference, abs(milp_value - benders_value))
        if milp_value <= data.target_coverage + 1e-6:
            brute_force_objective = min(brute_force_objective, sum(bits))

    milp_result = BilevelSolver(data, {"Benders": None, "TimeLimit": 60}).solve()
    benders_result = BilevelSolver(data, {"Benders": 1, "Degeneracy": 0, "TimeLimit": 60}).solve()
    if maximum_difference > 1e-6:
        raise AssertionError(f"Follower mismatch: {maximum_difference}")
    if milp_result["obj"] != brute_force_objective or benders_result["obj"] != brute_force_objective:
        raise AssertionError("Bilevel result differs from complete enumeration.")

    print(
        f"I={n_facilities}, J={n_demands}, seed={seed}: "
        f"enumeration={brute_force_objective:.0f}, "
        f"MILP={milp_result['obj']:.0f}, Benders={benders_result['obj']:.0f}, "
        f"max follower difference={maximum_difference:.2e}"
    )


def main():
    for case in ((5, 20, 0), (6, 25, 1), (7, 30, 2)):
        check_case(*case)


if __name__ == "__main__":
    main()
