import numpy as np

import gurobipy as gp
from gurobipy import GRB


class MasterProblem:

    def __init__(self, data, coefficient="critical"):

        self.data = data
        if coefficient not in {"global", "nogood", "critical"}:
            raise ValueError(f"Unknown interdiction-cut coefficient: {coefficient}")
        self.coefficient = coefficient

        self.model = gp.Model("MasterProblem")
        self.model.Params.OutputFlag = 0

        self._build_model()

    def _build_model(self):

        data = self.data

        self.x = self.model.addVars(data.I, vtype=GRB.BINARY, name="x")  # x_i = 1 if location i is blocked

        self.model.setObjective(
            gp.quicksum(data.blocker_cost[i] * self.x[i] for i in data.I),
            GRB.MINIMIZE
        )

        self.model.update()

    def compute_r_from_y_fast(self, y_val):

        data = self.data
        hat_y = np.where(y_val > 0.5)[0].astype(int)  # selected follower facilities

        r_val = np.full(len(data.J), np.inf, dtype=float)

        for i in hat_y:
            js = data.covered_demands[i]
            ps = data.covered_probs_arr[i]
            r_val[js] = np.minimum(r_val[js], ps)

        r_val[np.isinf(r_val)] = 0.0  # customers with no selected covering facility

        return r_val

    def solve(self):

        self.model.optimize()
        self.status = self.model.Status
        if self.status != GRB.OPTIMAL:
            return None, None

        x_val = {i: self.x[i].X for i in self.data.I}

        return x_val, self.data.target_coverage

    def generate_cut(self, y_star, r_star, ind):

        data = self.data
        hat_y = np.where(y_star > 0.5)[0].astype(int)  # selected follower facilities

        if ind is not None:
            revenue = float(r_star)
            r_val = self.compute_r_from_y_fast(y_star)
        else:
            r_val = r_star
            revenue = float(np.sum(data.demand_weight * r_val))

        if self.coefficient == "global":
            global_bound = float(np.sum(data.demand_weight))
            penalty_expr = global_bound * gp.quicksum(self.x[int(i)] for i in hat_y)
            return penalty_expr >= revenue - data.target_coverage

        if self.coefficient == "nogood":
            penalty_expr = revenue * gp.quicksum(self.x[int(i)] for i in hat_y)
            return penalty_expr >= revenue - data.target_coverage

        tol = 1e-5  # tolerance for critical-facility identification
        penalty_terms = []

        for i in hat_y:
            js = data.covered_demands[i]
            ps = data.covered_probs_arr[i]
            wps = data.covered_wprob_arr[i]

            critical_mask = np.abs(r_val[js] - ps) <= tol
            Mcrit_i = float(np.sum(wps[critical_mask]))  # critical coefficient M_i^-(y)

            if Mcrit_i > 0.0:
                penalty_terms.append(Mcrit_i * self.x[int(i)])

        penalty_expr = gp.quicksum(penalty_terms)

        return penalty_expr >= revenue - data.target_coverage

    def add_cut(self, cut_expr):

        self.model.addConstr(cut_expr)
        self.model.update()
