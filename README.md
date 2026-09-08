# Bilevel-MMCLBP

Replication code for *An Exact Algorithm for the Max--Min Covering Location
Blocker Problem* by Yun-Tian Zhang, Fabio Furini, Ivana Ljubić, and Chen Chen.
The package contains the exact value-function algorithm, its direct-MILP and
closed-form Benders follower variants, synthetic-instance generators, and the
Virginia Beach case-study workflow.

## Cite

If you use this code, please cite the associated manuscript and identify this
repository by its commit hash. A permanent software citation will be added
when the archival version is released.

```bibtex
@software{zhang2026bilevelmmclbp,
  author = {Zhang, Yun-Tian and Furini, Fabio and Ljubić, Ivana and Chen, Chen},
  title = {Bilevel-MMCLBP: Replication Code for the Max--Min Covering Location Blocker Problem},
  year = {2026},
  url = {https://github.com/Yuntian-Zhang/Bilevel-MMCLBP}
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

`make smoke` compares the Benders follower, the direct MILP follower, and
brute-force enumeration on small instances. It is the recommended first check
after installation.

## Documentation

- [Documentation home](docs/index.md)
- [Installation](docs/installation.md)
- [Inputs and outputs](docs/input_output.md)
- [Synthetic instances and benchmark design](docs/synthetic_instances.md)
- [Replicating tables and result files](docs/replication.md)
- [Virginia Beach case study](docs/virginia_beach.md)
- [Validation](docs/validation.md)

## Repository layout

```text
data/       generators and case-study data
solver/     outer master and follower implementations
scripts/    reproducible experiment entry points
tests/      automated exactness tests
docs/       detailed documentation
results/    locally generated CSV outputs
```

## Support

Please open an issue with the command, operating system, Python version,
Gurobi version, and complete error output.

## License

The source code is distributed under the [MIT License](LICENSE). The bundled
Virginia Beach workbook retains its own attribution and upstream license in
`data/virginia_beach/`.
