# Virginia Beach replication data

`VBOHCAR.xlsx` contains the 40 candidate base stations and 2,706 OHCA events
used by `scripts/reproduce_virginia_beach.py`. The experiment recomputes
Haversine distances from the latitude and longitude columns; it does not use
road distances from the workbook.

The file is an unmodified copy of the `VBOHCAR.xlsx` dataset distributed by
Custodio and Lejeune in the public VBOHCA repository. Please retain the
attribution and the upstream MIT license in `UPSTREAM_LICENSE` when reusing
or redistributing the data.
