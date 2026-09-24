# Documentation

This documentation describes how to install, validate, and reproduce the
computational results of the paper
[arXiv:2609.28084](https://arxiv.org/abs/2609.28084).

| Topic | Contents |
| --- | --- |
| [Installation](installation.md) | Software requirements, Gurobi, and C++ compilation |
| [Inputs and outputs](input_output.md) | CLI arguments, parameters, status fields, and CSV schema |
| [Synthetic instances](synthetic_instances.md) | Generator, seeds, and benchmark design |
| [Replication](replication.md) | Commands that regenerate result CSV files and tables |
| [Virginia Beach](virginia_beach.md) | Data provenance and the case-study workflow |
| [Validation](validation.md) | Automated tests and expected values |
| [General-purpose solvers](general_purpose_solvers.md) | Comparison with HC++ and MibS, Appendix A |

Start with [installation](installation.md), run the [validation](validation.md)
checks, and then select the required replication workflow.
