# Virginia Beach case study

The workflow uses `data/virginia_beach/VBOHCAR.xlsx`, containing 40 candidate
base stations and 2,706 OHCA events. The bundled workbook is an unmodified copy
of `results/VBOHCAR.xlsx` from the public
[VBOHCA repository](https://github.com/janielecustodio/VBOHCA). Its attribution
and upstream MIT license are retained in `data/virginia_beach/`.

The loader in `data/virginia_beach.py` recomputes every base-event Haversine
distance from latitude and longitude. It applies the same coverage rule as the
synthetic generator with:

| Parameter | Value |
| --- | ---: |
| Full-coverage radius | 4 km |
| Maximum-coverage radius | 8 km |
| Decay rate | 0.5 |
| Facility and blocker cost | 1 |
| Follower budget | 10 |
| Target coefficient | 0.7 |

Run the case study with:

```bash
python3 scripts/reproduce_virginia_beach.py --timelimit 7200
```

The script first obtains the unblocked follower value with the
branch-and-Benders-cut algorithm, then sets `t = 0.7 D0` and solves the blocker
problem with `OD+B&BC`. It checks that the unblocked value is approximately `1775.42` before
the blocker solve. Use `--skip-reference-check` only when deliberately using a
different workbook or parameterization.
