import itertools
import math

from data.data import Data
from data.virginia_beach import load_virginia_beach_instance
from solver.bilevel_solver import BilevelSolver
from solver.sub_problem import SubProblem, SubProblemOri


def test_benders_matches_milp_and_enumeration():
    data = Data()
    data.generate_random_instance(5, 20, 4, 8, 0.5, seed=0)
    unblocked = SubProblemOri(data, None)
    _, _, d0 = unblocked.solve()
    data.target_coverage = 0.7 * d0

    milp_follower = SubProblemOri(data, None)
    benders_follower = SubProblem(data, None, {"Degeneracy": 0})
    brute_force_objective = math.inf

    for bits in itertools.product((0, 1), repeat=len(data.I)):
        x = dict(enumerate(bits))
        milp_follower.update_x(x)
        _, _, milp_value = milp_follower.solve()
        benders_follower.update_x(x)
        _, _, benders_value = benders_follower.solve()
        assert abs(milp_value - benders_value) <= 1e-6
        if milp_value <= data.target_coverage + 1e-6:
            brute_force_objective = min(brute_force_objective, sum(bits))

    result = BilevelSolver(data, {"Benders": 1, "Degeneracy": 0, "TimeLimit": 60}).solve()
    assert result["status"] == "Optimal"
    assert result["obj"] == brute_force_objective


def test_virginia_beach_loader_dimensions():
    data = load_virginia_beach_instance("data/virginia_beach/VBOHCAR.xlsx")
    assert len(data.I) == 40
    assert len(data.J) == 2706
    assert data.facility_budget == 10
    assert data.prob.shape == (40, 2706)
