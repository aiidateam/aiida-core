#!/usr/bin/env bash
set -ev

# Make sure the folder containing the workchains is in the python path before the daemon is started
SYSTEM_TESTS="${GITHUB_WORKSPACE}/.github/system_tests"
MODULE_POLISH="${GITHUB_WORKSPACE}/.molecule/default/files/polish"

export PYTHONPATH="${PYTHONPATH}:${SYSTEM_TESTS}:${MODULE_POLISH}"

verdi daemon start 4
verdi -p test_aiida run ${SYSTEM_TESTS}/test_daemon.py
verdi -p test_aiida run ${SYSTEM_TESTS}/test_containerized_code.py
bash ${SYSTEM_TESTS}/test_polish_workchains.sh
verdi daemon stop
