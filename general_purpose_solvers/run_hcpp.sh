#!/usr/bin/env bash
# Run the general-purpose bilevel solver of Fischetti, Ljubic, Monaci and Sinnl
# on the exported MMCLBP instances and compare with the reference optima.
#   usage: HCPP_DIR=/path/to/solver ./run_hcpp.sh [setting] [timelimit] [pattern]
# HCPP_DIR is the directory containing the binary `bilevel`, the CPLEX dynamic
# libraries and the license file obtained from the authors (none of them is
# distributed with this repository).
# Settings: 98 = HC, 99 = HC++ (the only ones applicable to the MMCLBP; every
# intersection-cut and XU setting refuses the instance because the follower
# constraints are not all-integer).
set -u
export LC_ALL=C
DIST=${HCPP_DIR:?set HCPP_DIR to the directory of the solver binary}
SET=${1:-99}
TL=${2:-600}
PAT=${3:-'*'}
HERE=$(cd "$(dirname "$0")" && pwd)

printf '%-20s %5s %8s %10s %9s %8s %7s %s\n' \
    instance ref zbest 'root bnd' 'time (s)' nodes opt status
printf '%s\n' "-------------------------------------------------------------------------------"
for mps in "$HERE"/instances/$PAT.mps; do
  name=$(basename "$mps" .mps)
  ref=$(cat "$HERE"/instances/*_optima.csv | tr -d '\r' \
        | awk -F, -v n="$name" '$1==n{print $7}')
  [ -z "$ref" ] && continue
  log=$(mktemp)
  ( cd "$DIST" && LD_LIBRARY_PATH=. timeout $((TL + 60)) ./bilevel \
      -mpsfile "$HERE/instances/$name.mps" \
      -auxfile "$HERE/instances/$name.aux" \
      -setting "$SET" -time_limit "$TL" -print_sol 0 \
      -num_threads 1 -randomseed -1 ) >"$log" 2>&1
  rc=$?
  stat=$(grep -m1 '^ *STAT;' "$log")
  err=$(grep -m1 'ERROR' "$log" | sed 's/.*ERROR: *//')
  if [ -n "$stat" ]; then
    z=$(echo "$stat"  | awk -F';' '{gsub(/ /,"",$3); print $3}')
    rb=$(echo "$stat" | awk -F';' '{gsub(/ /,"",$5); print $5}')
    tm=$(echo "$stat" | awk -F';' '{gsub(/ /,"",$6); print $6}')
    nd=$(echo "$stat" | awk -F';' '{gsub(/ /,"",$9); print $9}')
    op=$(echo "$stat" | awk -F';' '{gsub(/ /,"",$8); print $8}')
    zi=$(printf '%.0f' "$z" 2>/dev/null)
    # opt: 1 = optimality proven, 0 = stopped at the time limit with an incumbent
    if [ "$op" = "1" ] && [ "$zi" = "$ref" ]; then st="opt"
    elif [ "$op" = "1" ]; then st="WRONG (proven $zi, optimum $ref)"
    elif awk -v v="$z" 'BEGIN{exit !(v>1e18)}'; then st="time limit, no solution"
    else st="time limit, incumbent $zi"; fi
    printf '%-20s %5s %8.2f %10.3f %9.2f %8s %7s %s\n' \
        "$name" "$ref" "$z" "$rb" "$tm" "$nd" "$op" "$st"
  elif [ $rc -eq 124 ]; then
    printf '%-20s %5s %8s %10s %9s %8s %7s %s\n' "$name" "$ref" - - - - - "hard timeout"
  else
    printf '%-20s %5s %8s %10s %9s %8s %7s %s\n' \
        "$name" "$ref" - - - - - "${err:-no STAT line}"
  fi
  rm -f "$log"
done
