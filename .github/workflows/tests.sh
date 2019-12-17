#!/usr/bin/env bash
set -ev

# Make sure the folder containing the workchains is in the python path before the daemon is started
export PYTHONPATH="${PYTHONPATH}:${GITHUB_WORKSPACE}/.ci"
# show timings of tests
export PYTEST_ADDOPTS=" --durations=0"

verdi daemon start 4
verdi -p test_${AIIDA_TEST_BACKEND} run .ci/test_daemon.py
verdi daemon stop

AIIDA_TEST_PROFILE=test_$AIIDA_TEST_BACKEND pytest
AIIDA_TEST_PROFILE=test_$AIIDA_TEST_BACKEND pytest .ci/pytest
pytest --noconftest .ci/test_test_manager.py
pytest --noconftest .ci/test_profile_manager.py

python .ci/test_plugin_testcase.py
