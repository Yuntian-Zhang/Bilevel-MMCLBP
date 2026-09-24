#!/usr/bin/env bash
# Run both general-purpose solvers over the whole grid, N jobs in parallel.
#
# Each job is one (solver, instance) pair and writes a single line, in the
# format make_comparison_table.py expects, under runs/parts/; the parts are
# concatenated into runs/hcpp.txt and runs/mibs.txt at the end.
#
#   usage: HCPP_DIR=/path/to/solver MIBS_DIR=/path/to/mibs/dist \
#          ./run_all.sh [parallel_jobs] [timelimit]
#
# The solvers are single-threaded, so a handful of concurrent jobs on a
# many-core machine does not distort the reported times.
set -u
export LC_ALL=C
HERE=$(cd "$(dirname "$0")" && pwd)
JOBS=${1:-4}
TL=${2:-600}
export HERE TL

mkdir -p "$HERE/runs/parts"
rm -f "$HERE/runs/parts"/*

joblist=$(mktemp)
for mps in "$HERE"/instances/mmclbp_m*_s0.mps; do
  name=$(basename "$mps" .mps)
  printf '%s %s\n%s %s\n' hcpp "$name" mibs "$name" >> "$joblist"
done
echo "$(wc -l < "$joblist") jobs, $JOBS at a time, ${TL}s limit"

xargs -a "$joblist" -P "$JOBS" -n 2 sh -c '
  case "$1" in
    hcpp) "$HERE/run_hcpp.sh" 99 "$TL" "$2" | tail -n +3 > "$HERE/runs/parts/hcpp_$2.txt" ;;
    mibs) "$HERE/run_mibs.sh"    "$TL" "$2" | tail -n +3 > "$HERE/runs/parts/mibs_$2.txt" ;;
  esac
  echo "done: $1 $2"
' sh

cat "$HERE"/runs/parts/hcpp_*.txt > "$HERE/runs/hcpp.txt"
cat "$HERE"/runs/parts/mibs_*.txt > "$HERE/runs/mibs.txt"
echo "ALL DONE"
