import numpy as np


class Data:

    def __init__(self):

        self.I = None  # facility locations
        self.J = None  # customers

        self.facility_cost = None
        self.facility_budget = None
        self.blocker_cost = None
        self.target_coverage = None
        self.demand_weight = None

        self.facility_coord = None
        self.demand_coord = None

        self.coverage_radius = None
        self.max_coverage_radius = None
        self.decay_rate = None

        self.bigM = None

    # ============================================================
    # instance generation
    # ============================================================

    def generate_random_instance(
        self,
        n_facilities=10,
        n_demands=10,
        coverage_radius=4,
        max_coverage_radius=8,
        decay_rate=0.5,
        seed=0
    ):

        np.random.seed(seed)

        self.coverage_radius = coverage_radius
        self.max_coverage_radius = max_coverage_radius
        self.decay_rate = decay_rate

        self.I = list(range(n_facilities))
        self.J = list(range(n_demands))

        self.facility_coord = 30 * np.random.rand(n_facilities, 2)  # 30 x 30 square
        self.demand_coord = 30 * np.random.rand(n_demands, 2)

        self.demand_weight = np.random.randint(1, 6, size=len(self.J))

        self.facility_cost = np.ones(len(self.I), dtype=int)
        self.blocker_cost = np.ones(len(self.I), dtype=int)
        self.facility_budget = int(0.2 * n_facilities)  # follower budget

        self.target_coverage = 0.0  # set after solving the unblocked follower

        self._compute_distance_matrix()

        self._compute_coverage_matrix()
        self._build_cover_sets()

        self.bigM = np.asarray(self.prob @ self.demand_weight, dtype=np.float64)  # M_i = sum_{j in J_i} d_j p_ij

    # ============================================================
    # distance matrix
    # ============================================================

    def _compute_distance_matrix(self):

        diff = self.facility_coord[:, np.newaxis, :] - self.demand_coord[np.newaxis, :, :]
        self.distance = np.sqrt(np.sum(diff ** 2, axis=2))

    # ============================================================
    # coverage matrix
    # ============================================================

    def _compute_coverage_matrix(self):

        d = self.distance
        r1 = self.coverage_radius
        r2 = self.max_coverage_radius
        alpha = self.decay_rate

        self.prob = np.where(
            d <= r1, 1.0,
            np.where(
                d <= r2,
                np.exp(-alpha * (d - r1)),
                0.0
            )
        )

    # ============================================================
    # utility functions
    # ============================================================

    def _build_cover_sets(self):

        eps = 1e-9
        rows, cols = np.where(self.prob > eps)

        temp_f = [[] for _ in range(len(self.J))]
        temp_d = [[] for _ in range(len(self.I))]

        for i, j in zip(rows, cols):
            temp_f[j].append(i)
            temp_d[i].append(j)

        self.covering_facilities = [np.array(lst, dtype=np.int32) for lst in temp_f]
        self.covered_demands = [np.array(lst, dtype=np.int32) for lst in temp_d]

        # Precompute arrays for fast critical-M computation
        self.covered_probs_arr = []
        self.covered_wprob_arr = []

        for i in range(len(self.I)):
            js = self.covered_demands[i]
            ps = self.prob[i, js].astype(float)
            wps = (self.demand_weight[js] * ps).astype(float)

            self.covered_probs_arr.append(ps)
            self.covered_wprob_arr.append(wps)

    def get_covering_facilities(self, j):
        return self.covering_facilities[j]

    def get_covered_demands(self, i):
        return self.covered_demands[i]

    # ============================================================
    # print summary
    # ============================================================

    def print_summary(self):

        print("========== Data Summary ==========")

        print(f"#facilities: {len(self.I)}")
        print(f"#demands: {len(self.J)}")

        print("==================================")
