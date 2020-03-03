#!/usr/bin/env bash
set -ev

# Make sure the folder containing the workchains is in the python path before the daemon is started
export PYTHONPATH="${PYTHONPATH}:${GITHUB_WORKSPACE}/.ci"

# pytest options:
# - report timings of tests
# - pytest-cov configuration taken from top-level .coveragerc
# - coverage is reported as XML and in terminal,
#   including the numbers/ranges of lines which are not covered
# - coverage results of multiple tests are collected
# - coverage is reported on files in aiida/
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --durations=0 --cov-config=.coveragerc --cov-report xml --cov-report term-missing --cov-append --cov=aiida"

# daemon tests
verdi daemon start 4
verdi -p test_${AIIDA_TEST_BACKEND} run .ci/test_daemon.py
verdi daemon stop

# tests for the testing infrastructure
pytest --noconftest .ci/test_test_manager.py
pytest --noconftest .ci/test_profile_manager.py
python .ci/test_plugin_testcase.py  # uses custom unittest test runner
AIIDA_TEST_PROFILE=test_$AIIDA_TEST_BACKEND pytest .ci/pytest

# main aiida-core tests
AIIDA_TEST_PROFILE=test_$AIIDA_TEST_BACKEND pytest tests
