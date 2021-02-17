#!/usr/bin/env bash
set -ev

# Make sure the folder containing the workchains is in the python path before the daemon is started
SYSTEM_TESTS="${GITHUB_WORKSPACE}/.github/system_tests"

export PYTHONPATH="${PYTHONPATH}:${SYSTEM_TESTS}"

# pytest options:
# - report timings of tests
# - pytest-cov configuration taken from top-level .coveragerc
# - coverage is reported as XML and in terminal,
#   including the numbers/ranges of lines which are not covered
# - coverage results of multiple tests (within a single GH Actions CI job) are collected
# - coverage is reported on files in aiida/
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --durations=50"
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --cov-config=${GITHUB_WORKSPACE}/.coveragerc"
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --cov-report xml"
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --cov-append"
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --cov=aiida"
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --verbose"

# daemon tests
verdi daemon start 4
verdi -p test_${AIIDA_TEST_BACKEND} run ${SYSTEM_TESTS}/test_daemon.py
verdi daemon stop

# tests for the testing infrastructure
pytest --noconftest ${SYSTEM_TESTS}/test_test_manager.py
pytest --noconftest ${SYSTEM_TESTS}/test_ipython_magics.py
pytest --noconftest ${SYSTEM_TESTS}/test_profile_manager.py
python ${SYSTEM_TESTS}/test_plugin_testcase.py  # uses custom unittest test runner

# Until the `${SYSTEM_TESTS}/pytest` tests are moved within `tests` we have to run them separately and pass in the path to the
# `conftest.py` explicitly, because otherwise it won't be able to find the fixtures it provides
AIIDA_TEST_PROFILE=test_$AIIDA_TEST_BACKEND pytest tests/conftest.py ${SYSTEM_TESTS}/pytest

# main aiida-core tests
AIIDA_TEST_PROFILE=test_$AIIDA_TEST_BACKEND pytest tests
