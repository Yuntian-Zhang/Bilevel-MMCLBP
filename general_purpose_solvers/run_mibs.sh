#!/usr/bin/env bash
# Run the open-source general-purpose bilevel solver MibS on the exported
# MMCLBP instances and compare with the reference optima.
#   usage: MIBS_DIR=/path/to/mibs/dist ./run_mibs.sh [timelimit] [pattern]
# MIBS_DIR is the installation directory of MibS (with bin/ and lib/).
set -u
export LC_ALL=C
DIST=${MIBS_DIR:?set MIBS_DIR to the MibS dist directory}
TL=${1:-300}
PAT=${2:-'*'}
HERE=$(cd "$(dirname "$0")" && pwd)
export LD_LIBRARY_PATH=$DIST/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}

printf '%-20s %6s %10s %8s %8s %9s %8s %8s\n' instance ref mibs time status VFsolved cuts nodes
printf '%s\n' "----------------------------------------------------------------------------"
for mps in "$HERE"/instances/$PAT.mps; do
  name=$(basename "$mps" .mps)
  ref=$(cat "$HERE"/instances/*_optima.csv | tr -d '\r' \
        | awk -F, -v n="$name" '$1==n{print $7}')
  [ -z "$ref" ] && continue
  log=$(mktemp)
  start=$(date +%s.%N)
  timeout $((TL + 30)) "$DIST/bin/mibs" \
      -Alps_instance "$mps" \
      -MibS_auxiliaryInfoFile "$HERE/instances/$name.aux" \
      -Alps_timeLimit "$TL" >"$log" 2>&1
  rc=$?
  el=$(echo "$(date +%s.%N) - $start" | bc)
  cost=$(grep -m1 '^Cost = ' "$log" | awk '{print $3}')
  vf=$(grep -m1 'problems (VF) solved' "$log" | awk -F= '{print $2}' | tr -d ' ')
  nd=$(grep -m1 'Number of nodes fully processed' "$log" | awk '{print $NF}')
  cuts=$(grep -c 'Cuts Generated' "$log")
  ncut=$(awk -F: '/Cuts Generated|No Good Cuts Generated|Binary Cuts Generated/{s+=$2}END{print s+0}' "$log")
  if [ $rc -eq 124 ]; then st=timeout; cost=${cost:-"-"}
  elif [ -z "${cost:-}" ]; then st=fail
  elif [ "$cost" = "$ref" ]; then st=match
  else st=MISMATCH; fi
  printf '%-20s %6s %10s %8.2f %8s %9s %8s %8s\n' \
      "$name" "$ref" "${cost:--}" "$el" "$st" "${vf:--}" "${ncut:--}" "${nd:--}"
  rm -f "$log"
done
