#!/usr/bin/env bash
set -e

# Test the loading time of `verdi`. This is and attempt to catch changes to the imports in `aiida.cmdline` that will
# indirectly load the `aiida.orm` module which will trigger loading of the backend environment. This slows down `verdi`
# significantly, making tab-completion unusable.
VERDI=`which verdi`

# Typically, the loading time of `verdi` should be around ~0.2 seconds. When loading the database environment this
# tends to go towards ~0.8 seconds. Since these timings are obviously machine and environment dependent, typically these
# types of tests are fragile. But with a load limit of more than twice the ideal loading time, if exceeded, should give
# a reasonably sure indication that the loading of `verdi` is unacceptably slowed down.
LOAD_LIMIT=0.4
MAX_NUMBER_ATTEMPTS=5

iteration=0

while true; do

    iteration=$((iteration+1))
    load_time=$(/usr/bin/time -q -f "%e" $VERDI 2>&1 > /dev/null)

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
