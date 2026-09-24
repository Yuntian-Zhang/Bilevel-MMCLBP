# Synthetic instances and benchmark design

The synthetic generator is implemented in `data/data.py`. It samples candidate
facilities and customers uniformly in a 30 by 30 square, then draws demand
weights independently from the discrete uniform distribution on `{1, …, 5}`.

For a facility-customer distance `d`, coverage is

```text
1                         if d <= r1
exp(-lambda * (d - r1))   if r1 < d <= r2
0                         otherwise
```

The baseline uses `r1 = 4`, `r2 = 8`, `lambda = 0.5`, unit facility and
blocker costs, a follower budget `floor(0.2 * |I|)`, and `beta = 0.7`.
Each seed deterministically regenerates the corresponding instance.

The main benchmark contains 13 `(facilities, demands)` classes and five seeds
per class. The first three seeds of the compact diagnostic classes have these
optimal blocker objectives:

| Facilities | Demands | Seeds 0, 1, 2 |
| ---: | ---: | --- |
| 20 | 20,000 | 9, 5, 7 |
| 25 | 20,000 | 9, 7, 9 |
