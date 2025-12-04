#!/usr/bin/env bash

set -euo pipefail

verdi devel check-load-time
verdi devel check-undesired-imports

# Test the loading time of `verdi`. This is an attempt to catch changes to the imports in `aiida.cmdline` that
# would slow down `verdi` invocations and make tab-completion unusable.
VERDI=`which verdi`

# Typically, the loading time of `verdi` should be around <0.2 seconds.
# Typically these types of tests are fragile. But with a load limit of more than twice
# the ideal loading time, if exceeded, should give a reasonably sure indication
# that the loading of `verdi` is unacceptably slowed down.
LOAD_LIMIT=0.3
MAX_NUMBER_ATTEMPTS=5

iteration=0

while true; do

    iteration=$((iteration+1))
    load_time=$(/usr/bin/time -q -f "%e" $VERDI -h 2>&1 > /dev/null)

    if (( $(echo "$load_time < $LOAD_LIMIT" | bc -l) )); then
        echo "SUCCESS: loading time $load_time at iteration $iteration below $LOAD_LIMIT"
        break
    else
        echo "WARNING: loading time $load_time at iteration $iteration above $LOAD_LIMIT"

        if [ $iteration -eq $MAX_NUMBER_ATTEMPTS ]; then
            echo "ERROR: loading time exceeded the load limit $iteration consecutive times."
            echo "ERROR: please check that 'aiida.cmdline' does not import 'aiida.orm' at module level, even indirectly"
            echo "ERROR: also, the database backend environment should not be loaded."
            exit 2
        fi
    fi

done

# Test that we can also run the CLI via `python -m aiida`,
# that it returns a 0 exit code, and contains the expected stdout.
echo "Invoking verdi via 'python -m aiida -h'"
OUTPUT=$(python -m aiida -h 2>&1)
RETVAL=$?
if [ $RETVAL -ne 0 ]; then
    echo "'python -m aiida' exitted with code $RETVAL"
    echo "=== OUTPUT ==="
    echo $OUTPUT
    exit 2
fi
if [[ $OUTPUT != *"command line interface of AiiDA"* ]]; then
    echo "'python -m aiida' did not contain the expected stdout:"
    echo "=== OUTPUT ==="
    echo $OUTPUT
    exit 2
fi
