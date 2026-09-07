import time
import numpy as np

import gurobipy as gp
from gurobipy import GRB

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import fast_sep


class SubProblem:

    def __init__(self, data, bigM, params=None):

        self.data = data

        self.params = params if params is not None else {}

        self.M = bigM

        self.I = data.I
        self.J = data.J
        self.p = data.prob
        self.d = data.demand_weight

        self.Ij = {
            j: list(data.get_covering_facilities(j))
            for j in self.J
        }

        # ============================================================
        # follower model for Benders decomposition -> project out r
        # ============================================================

        self.model = gp.Model("Benders_Follower")

        self.model.Params.OutputFlag = 0
        self.model.Params.LazyConstraints = 1
        self.model.Params.PreCrush = 1

        self.y = self.model.addVars(data.I, vtype=GRB.BINARY, name="y")
        self.theta = self.model.addVar(vtype=GRB.CONTINUOUS,
                                       lb=0.0, ub=sum(self.data.demand_weight[j] for j in self.data.J), name="theta")

        self.model.setObjective(self.theta, GRB.MAXIMIZE)

        self.model.addConstr(gp.quicksum(data.facility_cost[i] * self.y[i] for i in data.I) \
                             <= data.facility_budget, name="budget")

        # Attach data to the Gurobi model for callback access
        self.model._M = self.M
        self.model._y = self.y
        self.model._theta = self.theta
        self.model._I = self.I
        self.model._J = self.J
        self.model._p = self.p
        self.model._d = self.d
        self.model._Ij = self.Ij
        self.model._degeneracy = bool(self.params.get("Degeneracy", False))

        self._prepare_fast_separation_data()

    def _prepare_fast_separation_data(self):

        # Build CSR-style arrays for the C++ separator
        indptr = [0]
        indices = []
        pval = []

        for j in self.data.J:
            for i in self.model._Ij[j]:
                indices.append(int(i))
                pval.append(float(self.model._p[i, j]))
            indptr.append(len(indices))

        self.model._indptr = np.array(indptr, dtype=np.int32)
        self.model._indices = np.array(indices, dtype=np.int32)
        self.model._pval = np.array(pval, dtype=np.float64)

        self.model._d_np = np.ascontiguousarray(
            self.model._d,
            dtype=np.float64
        )

        self.model._y_list = [
            self.model._y[i]
            for i in self.data.I
        ]

    @staticmethod
    def benders_callback(model, where):

        if not hasattr(SubProblem.benders_callback, 'initialized'):
            SubProblem.benders_callback.integer_cuts = 0
            SubProblem.benders_callback.fractional_cuts = 0
            SubProblem.benders_callback.bb_nodes = 0
            SubProblem.benders_callback.integer_time = 0.0
            SubProblem.benders_callback.fractional_time = 0.0
            SubProblem.benders_callback.initialized = True

        if where == GRB.Callback.MIPSOL:
            t0 = time.perf_counter()
            n_added = SubProblem.separate(model, integer=True)
            SubProblem.benders_callback.integer_time += time.perf_counter() - t0
            SubProblem.benders_callback.integer_cuts += n_added
        elif where == GRB.Callback.MIPNODE:
            node_cnt = model.cbGet(GRB.Callback.MIPNODE_NODCNT)
            SubProblem.benders_callback.bb_nodes = max(SubProblem.benders_callback.bb_nodes, node_cnt)
            # status = model.cbGet(GRB.Callback.MIPNODE_STATUS)
            # if status == GRB.OPTIMAL:
            #     t0 = time.perf_counter()
            #     SubProblem.separate(model, integer=False)
            #     SubProblem.benders_callback.fractional_time += time.perf_counter() - t0
            #     SubProblem.benders_callback.fractional_cuts += 1

    @staticmethod
    def separate(model, integer):

        n_added = 0

        if integer:
            y_val = model.cbGetSolution(model._y)
            theta_val = model.cbGetSolution(model._theta)
        else:
            y_val = model.cbGetNodeRel(model._y)
            theta_val = model.cbGetNodeRel(model._theta)

        y_np = np.array([y_val[i] for i in model._I], dtype=np.float64)

        if not model._degeneracy:

            res = fast_sep.separate_cbc(
                y_np,
                float(theta_val),
                model._indptr,
                model._indices,
                model._pval,
                model._d_np,
                1e-6
            )

            if not res["violated"]:
                return 0

            const_term = float(res["const"])
            idx = res["idx"]
            coef = res["coef"]

            lhs = const_term + gp.quicksum(
                float(c) * model._y_list[int(i)]
                for i, c in zip(idx, coef)
            )

            if integer:
                model.cbLazy(lhs >= model._theta)
                n_added += 1

        else:

            res = fast_sep.separate_cbc_dual_degeneracy(
                y_np,
                float(theta_val),
                model._indptr,
                model._indices,
                model._pval,
                model._d_np,
                1e-6,  # tol
                1e-8  # duplicate_tol
            )

            if not bool(res["violated"]):
                return 0

            base_const = float(res["const"])
            base_idx = res["idx"]
            base_coef = res["coef"]

            lhs_base = base_const + gp.quicksum(
                float(c) * model._y[int(i)]
                for i, c in zip(base_idx, base_coef)
            )

            model.cbLazy(lhs_base >= model._theta)
            n_added += 1

            if bool(res["has_alt"]):
                delta_const = float(res["delta_const"])
                delta_idx = res["delta_idx"]
                delta_coef = res["delta_coef"]

                delta_expr = delta_const + gp.quicksum(
                    float(c) * model._y[int(i)]
                    for i, c in zip(delta_idx, delta_coef)
                )

                lhs_alt = lhs_base + delta_expr
                model.cbLazy(lhs_alt >= model._theta)
                n_added += 1

        return n_added

    def update_x(self, x_fixed):

        # Blocked locations are unavailable to the follower
        for i in self.data.I:
            if float(x_fixed[i]) > 0.5:
                self.y[i].UB = 0.0
            else:
                self.y[i].UB = 1.0

        self.model.update()

    def solve(self):

        self.model.optimize(SubProblem.benders_callback)
        y_array = np.array([self.y[i].X for i in self.data.I])
        return y_array, self.theta.X, self.model.ObjVal


class SubProblemOri:

    def __init__(self, data, bigM, params=None):

        self.data = data

        self.params = params if params is not None else {}

        self.M = bigM

        self.I = data.I
        self.J = data.J
        self.p = data.prob
        self.d = data.demand_weight

        # ============================================================
        # original follower model
        # ============================================================

        self.model_ori = gp.Model("Follower")
        self.model_ori.Params.OutputFlag = 0

        self.y_ori = self.model_ori.addVars(data.I, vtype=GRB.BINARY, name="y")
        self.r = self.model_ori.addVars(data.J, vtype=GRB.CONTINUOUS, lb=0.0, ub=1.0, name="r")

        self.model_ori.setObjective(gp.quicksum(self.data.demand_weight[j] * self.r[j] for j in self.data.J),
                                    GRB.MAXIMIZE)

        self.model_ori.addConstr(gp.quicksum(data.facility_cost[i] * self.y_ori[i] for i in data.I) \
                             <= data.facility_budget, name="budget")
        for j in data.J:
            self.model_ori.addConstr(self.r[j] <= gp.quicksum(data.prob[i, j] * self.y_ori[i]
                                                          for i in data.get_covering_facilities(j)),
                                 name=f"r_sum_{j}")
        for j in data.J:
            for i in [i for i in data.get_covering_facilities(j)]:
                self.model_ori.addConstr(self.r[j] <= 1 - (1 - data.prob[i, j]) * self.y_ori[i],
                                         name=f"r_individual_{i}_{j}")

    def update_x(self, x_fixed):

        for i in self.data.I:
            if float(x_fixed[i]) > 0.5:
                self.y_ori[i].UB = 0.0
            else:
                self.y_ori[i].UB = 1.0

        self.model_ori.update()

    def solve(self):

        self.model_ori.optimize()
        y_array = np.array([self.y_ori[i].X for i in self.data.I])
        r_array = np.array([self.r[j].X for j in self.data.J])
        return y_array, r_array, self.model_ori.ObjVal
