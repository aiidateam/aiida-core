#!/usr/bin/env bash

# Be verbose, and stop with error as soon there's one
set -ev

declare -a EXPRESSIONS=("1 -2 -1 4 -5 -5 * * * * +" "2 1 3 3 -1 + ^ ^ +" "3 -5 -1 -4 + * ^" "2 4 2 -4 * * +" "3 1 1 5 ^ ^ ^" "3 1 3 4 -4 2 * + + ^ ^")
NUMBER_WORKCHAINS=5
TIMEOUT=600
CODE='add@torquessh'

# Needed on Jenkins
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

# Define the absolute path to the RPN cli script
DATA_DIR="${TRAVIS_BUILD_DIR}/.ci"
CLI_SCRIPT="${DATA_DIR}/polish/cli.py"

# Export the polish module to the python path so generated workchains can be imported
export PYTHONPATH="${PYTHONPATH}:${DATA_DIR}/polish"

# Get the absolute path for verdi
VERDI=$(which verdi)

if [ -n "$EXPRESSIONS" ]; then
    for expression in "${EXPRESSIONS[@]}"; do
        coverage run -a $VERDI -p ${TEST_AIIDA_BACKEND} run "${CLI_SCRIPT}" -c $CODE -C -W -d -t $TIMEOUT "$expression"
    done
else
    for i in $(seq 1 $NUMBER_WORKCHAINS); do
        coverage run -a $VERDI -p ${TEST_AIIDA_BACKEND} run "${CLI_SCRIPT}" -c $CODE -C -W -d -t $TIMEOUT
    done
fi