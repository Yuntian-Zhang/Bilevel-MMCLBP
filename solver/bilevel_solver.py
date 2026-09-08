import time
import math

from gurobipy import GRB

from solver.master_problem import MasterProblem
from solver.sub_problem import SubProblem, SubProblemOri


def _print_cut_stats():

    callback = SubProblem.benders_callback

    integer_cuts = getattr(callback, 'integer_cuts', 0)
    fractional_cuts = getattr(callback, 'fractional_cuts', 0)
    bb_nodes = getattr(callback, 'bb_nodes', 0)
    sep_integer_time = getattr(callback, 'integer_time', 0.0)
    sep_frac_time = getattr(callback, 'fractional_time', 0.0)

    print("=" * 50)
    print("CUT GENERATION STATISTICS")
    print("=" * 50)
    print(f"Integer cuts: {integer_cuts}")
    print(f"Fractional cuts: {fractional_cuts}")
    print(f"Total cuts: {integer_cuts + fractional_cuts}")
    print(f"Maximum BB nodes: {bb_nodes}")
    print(f"Integer-solution separation time: {sep_integer_time:.4f} s")
    print(f"Fractional-solution separation time: {sep_frac_time:.4f} s")
    print("=" * 50)


class BilevelSolver:

    def __init__(self, data, params=None):

        self.data = data

        self.params = params if params is not None else {}
        self.benders_callback = self.params.get("Benders", None)  # None: original follower; otherwise: Benders

        if self.benders_callback is not None:
            self.subproblem = SubProblem(data, self.data.bigM, self.params)
        else:
            self.subproblem = SubProblemOri(data, self.data.bigM, self.params)

        self.master = MasterProblem(data, self.params.get("Coefficient", "critical"))

        self.tol = 1e-6

        self.subp_count = 0

        self.time_limit = self.params.get("TimeLimit", 3600)
        self.master_time = 0.0
        self.subproblem_time = 0.0
        self.total_time = 0.0

        # all-blocked feasible incumbent
        self.incumbent_x = {i: 1.0 for i in self.data.I}
        self.incumbent_y = None
        self.incumbent_r = None
        self.incumbent_obj = float(sum(self.data.blocker_cost[i] for i in self.data.I))

        self.best_bound = None
        self.final_gap = None

        self.status = "NotSolved"

    def solve(self):

        start_time = time.time()
        self._start_time = start_time

        while True:

            elapsed = time.time() - start_time
            if elapsed >= self.time_limit:
                self.status = "TimeLimit"
                self.total_time = elapsed
                self._record_bound_and_gap()
                return self._return_incumbent_or_dummy()

            # ======================================================
            # Step 1: solve master
            # ======================================================

            self._set_time_limit_if_possible(
                self.master,
                self.time_limit - elapsed
            )
            t0 = time.time()
            x_star, t_val = self.master.solve()
            t1 = time.time()
            self.master_time += t1 - t0

            self._update_best_bound()

            if self.master.status != GRB.OPTIMAL:
                return self._return_after_solver_stop(self.master.status)

            elapsed = time.time() - start_time

            if elapsed >= self.time_limit:
                self.status = "TimeLimit"
                self.total_time = elapsed
                self._record_bound_and_gap()

                return self._return_incumbent_or_dummy()

            # ======================================================
            # Step 2: solve follower
            # ======================================================

            self.subproblem.update_x(x_star)
            self._set_time_limit_if_possible(
                self.subproblem,
                self.time_limit - elapsed
            )

            t0 = time.time()
            y_star, r_star, sp_obj = self.subproblem.solve()
            t1 = time.time()
            self.subproblem_time += t1 - t0
            self.subp_count += 1

            if self.subproblem.status != GRB.OPTIMAL:
                return self._return_after_solver_stop(self.subproblem.status)

            elapsed = time.time() - start_time

            if elapsed >= self.time_limit:
                self.status = "TimeLimit"
                self.total_time = elapsed
                self._record_bound_and_gap()

                return self._return_incumbent_or_dummy()

            # ======================================================
            # Step 3: check value-function violation
            # ======================================================

            violated = self._is_violated(t_val, sp_obj)
            if not violated:

                leader_obj = float(
                    sum(self.data.blocker_cost[i] * x_star[i] for i in self.data.I)
                )
                if leader_obj < self.incumbent_obj:
                    self.incumbent_x = x_star
                    self.incumbent_y = y_star
                    self.incumbent_r = r_star
                    self.incumbent_obj = leader_obj

                self.status = "Optimal"
                self.total_time = elapsed

                self._record_bound_and_gap()

                # _print_cut_stats()

                return {
                    "x": self.incumbent_x,
                    "y": self.incumbent_y,
                    "r": self.incumbent_r,
                    "obj": self.incumbent_obj,
                    "bound": self.best_bound,
                    "gap": self.final_gap,
                    "status": self.status,
                    "time": self.total_time
                }

            # ======================================================
            # Step 4: generate value-function inequality
            # ======================================================

            cut_expr = self.master.generate_cut(
                y_star,
                r_star,
                self.benders_callback
            )

            # ======================================================
            # Step 5: add inequality
            # ======================================================

            self.master.add_cut(cut_expr)

    def _is_violated(self, t_val, sp_obj):

        if t_val < sp_obj - self.tol:
            return True
        else:
            return False

    def _return_after_solver_stop(self, solver_status):

        self.total_time = time.time() - self._start_time
        self.status = "TimeLimit" if solver_status == GRB.TIME_LIMIT else f"SolverStatus_{solver_status}"
        self._record_bound_and_gap()
        return self._return_incumbent_or_dummy()

    def _record_bound_and_gap(self):

        if (
            self.incumbent_obj < float("inf")
            and self.best_bound is not None
        ):
            if abs(self.incumbent_obj) > self.tol:
                self.final_gap = max(
                    0.0,
                    (self.incumbent_obj - self.best_bound)
                    / abs(self.incumbent_obj)
                )
            elif abs(self.incumbent_obj - self.best_bound) <= self.tol:
                self.final_gap = 0.0
            else:
                self.final_gap = None
        else:
            self.final_gap = None

    def _update_best_bound(self):

        try:
            bound = float(self.master.model.ObjBound)
        except Exception:
            return

        if not math.isfinite(bound):
            return

        if self.best_bound is None:
            self.best_bound = bound
        else:
            self.best_bound = max(self.best_bound, bound)

    def _return_incumbent_or_dummy(self):

        if self.incumbent_x is not None:
            print(
                "[RETURN] Time limit reached. "
                "Return checked incumbent solution."
            )
            return {
                "x": self.incumbent_x,
                "y": self.incumbent_y,
                "r": self.incumbent_r,
                "obj": self.incumbent_obj,
                "bound": self.best_bound,
                "gap": self.final_gap,
                "status": self.status,
                "time": self.total_time
            }
        print(
            "[WARNING] Time limit reached before finding "
            "any checked feasible incumbent."
        )

        return {
            "x": None,
            "y": None,
            "r": None,
            "obj": None,
            "bound": self.best_bound,
            "gap": None,
            "status": self.status,
            "time": self.total_time
        }

    def _set_time_limit_if_possible(
        self,
        solver_obj,
        remaining_time
    ):

        if remaining_time <= 0:
            return

        for attr in ["model", "model_ori", "m"]:  # support alternative solver-model wrappers
            if hasattr(solver_obj, attr):
                getattr(solver_obj, attr).Params.TimeLimit = remaining_time
