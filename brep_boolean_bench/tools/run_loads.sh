#!/usr/bin/env bash
# Load every STEP of the bench on both kernels: ours raw, ours with driver-side REPAIR=1, OCCT (file units).
T=$(dirname "$0"); R=$T/../run; B=/home/user/session_data/brep_boolean_bench
PY=/tmp/claude-0/-home-user/8b288b7c-72c4-56e2-9565-a39939e050f9/scratchpad/ocp/venv/bin/python
FILES=$(find $B -name "*.st*p" | sort)
for f in $FILES; do ( ulimit -v 6000000; timeout 300 $T/ours_step_bench load $f 2>/dev/null | grep -a -E "^(LOAD|BREP|DIAG)"; echo "EXIT $f ${PIPESTATUS[0]}" ); done > $R/ours_load.txt
for f in $FILES; do ( ulimit -v 6000000; REPAIR=1 timeout 300 $T/ours_step_bench load $f 2>/dev/null | grep -a -E "^(LOAD|BREP|DIAG|REPAIR)"; echo "EXIT $f ${PIPESTATUS[0]}" ); done > $R/ours_load_repaired.txt
for f in $FILES; do timeout 300 $PY -I $T/occt_step_bench.py load $f 2>/dev/null | grep -a -E "^(LOAD|SOLID)"; done > $R/occt_load.txt
echo done
