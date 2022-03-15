#!/usr/bin/env bash
set -ev

# Make sure the folder containing the workchains is in the python path before the daemon is started
MODULE_POLISH="${GITHUB_WORKSPACE}/.molecule/default/files/polish"
CLI_SCRIPT="${MODULE_POLISH}/cli.py"

declare -a EXPRESSIONS=("1 -2 -1 4 -5 -5 * * * * +" "2 1 3 3 -1 + ^ ^ +" "3 -5 -1 -4 + * ^" "2 4 2 -4 * * +" "3 1 1 5 ^ ^ ^" "3 1 3 4 -4 2 * + + ^ ^")
NUMBER_WORKCHAINS=5
TIMEOUT=600
CODE='add!'  # Note the exclamation point is necessary to force the value to be interpreted as LABEL type identifier

# Get the absolute path for verdi
VERDI=$(which verdi)

if [ -n "$EXPRESSIONS" ]; then
    for expression in "${EXPRESSIONS[@]}"; do
        $VERDI -p test_aiida run "${CLI_SCRIPT}" -X $CODE -C -F -d -t $TIMEOUT "$expression"
    done
else
    for i in $(seq 1 $NUMBER_WORKCHAINS); do
        $VERDI -p test_aiida run "${CLI_SCRIPT}" -X $CODE -C -F -d -t $TIMEOUT
    done
fi
