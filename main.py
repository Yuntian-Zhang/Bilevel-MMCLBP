import time
import argparse

from data.data import Data
from solver.bilevel_solver import BilevelSolver
from solver.sub_problem import SubProblem


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("I", type=int)
    parser.add_argument("J", type=int)
    parser.add_argument("r1", type=float)
    parser.add_argument("r2", type=float)
    parser.add_argument("beta", type=float)
    parser.add_argument("benders", type=int, choices=[0, 1])
    parser.add_argument("seed", type=int)
    parser.add_argument("--degeneracy", type=int, choices=[0, 1], default=0)
    parser.add_argument("--coefficient", choices=["global", "nogood", "critical"], default="critical")
    parser.add_argument("--timelimit", type=float, default=3600)
    args = parser.parse_args()
    if args.degeneracy == 1 and args.benders == 0:
        parser.error("--degeneracy requires benders=1.")

    instances = [
        [args.I, args.J, args.r1, args.r2]
    ]
    seeds = [args.seed]

    for instance in instances:

        for seed in seeds:

            print("\n" + "=" * 70)
            print(f"Instance: I={instance[0]}, J={instance[1]}, seed={seed}")
            print("=" * 70)

            data = Data()
            data.generate_random_instance(
                n_facilities=instance[0],
                n_demands=instance[1],
                coverage_radius=instance[2],
                max_coverage_radius=instance[3],
                decay_rate=0.5,
                seed=seed
            )
            sum_cover_edges = sum(len(data.covering_facilities[j]) for j in data.J)
            cover_density = (sum_cover_edges / (len(data.I) * len(data.J)))
            # data.print_summary()
            print(f"Coverage edges: {sum_cover_edges}")
            print(f"Coverage density: {cover_density:.4f}")

            sub_unblocked = SubProblem(data, None)
            _, _, D0 = sub_unblocked.solve()
            print(f"Unblocked follower objective D0: {D0}")
            data.target_coverage = args.beta * D0  # Generate target coverage: t = beta * D0

            # Reset callback statistics
            SubProblem.benders_callback.integer_cuts = 0
            SubProblem.benders_callback.fractional_cuts = 0
            SubProblem.benders_callback.bb_nodes = 0
            SubProblem.benders_callback.integer_time = 0.0
            SubProblem.benders_callback.fractional_time = 0.0

            use_benders = 1 if args.benders == 1 else None
            params = {
                "Benders": use_benders,
                "Degeneracy": args.degeneracy,
                "Coefficient": args.coefficient,
                "TimeLimit": args.timelimit
            }
            solver = BilevelSolver(data, params=params)
            start = time.time()
            result = solver.solve()
            elapsed = time.time() - start

            print("=" * 50)
            print("Benders" if use_benders is not None else "No-Benders")
            print("=" * 50)
            print(f"Status: {result['status']}")
            print(f"Time: {elapsed:.4f}s")
            print(f"Incumbent objective: {result['obj']}")
            print(f"Best bound: {result['bound']}")
            print(f"Final gap: {result['gap']}")

            if use_benders is not None:

                int_b = SubProblem.benders_callback.integer_cuts
                bb_b = SubProblem.benders_callback.bb_nodes
                sep_int_t = SubProblem.benders_callback.integer_time

                eps = 1e-12
                print(f"Benders cuts: {int_b}")
                print(f"BB nodes: {bb_b}")
                print(f"Separation-time ratio: {sep_int_t / max(elapsed, eps):.4f}")


if __name__ == "__main__":
    main()
