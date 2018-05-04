#!/usr/bin/env bash
NUMBER_WORKCHAINS=5
TIMEOUT=240
CODE='add@torquessh'

# Be verbose, and stop with error as soon there's one
set -ev

# Needed on Jenkins
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

# Define the absolute path to the RPN cli script
JENKINS_DATA_DIR="${TRAVIS_BUILD_DIR}/.jenkins-data"
CLI_SCRIPT="${JENKINS_DATA_DIR}/polish/cli.py"

# Export the polish module to the python path so generated workchains can be imported
export PYTHONPATH="${PYTHONPATH}:${JENKINS_DATA_DIR}/polish"

# Get the absolute path for verdi
VERDI=$(which verdi)

for i in $(seq 1 $NUMBER_WORKCHAINS); do

    coverage run -a $VERDI -p ${TEST_AIIDA_BACKEND} run "${CLI_SCRIPT}" -c $CODE -C -W -d -t $TIMEOUT

done