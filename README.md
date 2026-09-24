# Bilevel-MMCLBP

Replication code for *An Exact Algorithm for the Max--Min Covering Location
Blocker Problem* by Yun-Tian Zhang, Chen Chen, Fabio Furini, and Ivana Ljubić.
The paper is available on arXiv:
[arXiv:2609.28084](https://arxiv.org/abs/2609.28084).

The package contains the exact algorithm `OD+B&BC`, an outer decomposition
with interdiction cuts whose follower problem is solved by a branch-and-Benders-cut
algorithm with closed-form separation, together with the `OD+MILP` variant,
in which the follower is solved directly as an MILP. It also contains the
synthetic-instance generators and the Virginia Beach case-study workflow.

## Cite

If you use this code, please cite the paper:

```bibtex
@misc{zhang2026exact,
  author = {Zhang, Yun-Tian and Chen, Chen and Furini, Fabio and Ljubić, Ivana},
  title = {An Exact Algorithm for the Max--Min Covering Location Blocker Problem},
  year = {2026},
  eprint = {2609.28084},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2609.28084}
}
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
make smoke
```

`make smoke` compares `OD+B&BC`, `OD+MILP`, and complete enumeration on
small instances. It is the recommended first check
after installation.

## Documentation

- [Documentation home](docs/index.md)
- [Installation](docs/installation.md)
- [Inputs and outputs](docs/input_output.md)
- [Synthetic instances and benchmark design](docs/synthetic_instances.md)
- [Replicating tables and result files](docs/replication.md)
- [Virginia Beach case study](docs/virginia_beach.md)
- [Validation](docs/validation.md)
- [Comparison with general-purpose bilevel solvers](docs/general_purpose_solvers.md)

## Repository layout

```text
data/       generators and case-study data
solver/     outer decomposition, relaxed master problem, and follower solvers
scripts/    reproducible experiment entry points
tests/      automated exactness tests
docs/       detailed documentation
results/    raw results reported in the paper (see results/results.md)
general_purpose_solvers/  instances and scripts for the comparison of Appendix A
```

## Support

Please open an issue with the command, operating system, Python version,
Gurobi version, and complete error output.

## License

The source code is distributed under the [MIT License](LICENSE). The bundled
Virginia Beach workbook retains its own attribution and upstream license in
`data/virginia_beach/`.
