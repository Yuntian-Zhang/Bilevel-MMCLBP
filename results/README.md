# Generated results

Experiment scripts write timestamped CSV files into `results/generated/`.
That directory is intentionally ignored by Git: it can contain large,
machine-specific outputs and is regenerated from the scripts and seeds.

Before an archival release, retain one validated set of raw CSV outputs and
commit it in a clearly named subdirectory together with the environment and
hardware details used to create it.
