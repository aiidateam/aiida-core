#!/usr/bin/env bash
set -ev

# Make sure the folder containing the workchains is in the python path before the daemon is started
SYSTEM_TESTS="${GITHUB_WORKSPACE}/.github/system_tests"
MODULE_POLISH="${GITHUB_WORKSPACE}/.molecule/default/files/polish"

export PYTHONPATH="${PYTHONPATH}:${SYSTEM_TESTS}:${MODULE_POLISH}"

# daemon tests
verdi daemon start 4
verdi -p test_${AIIDA_TEST_BACKEND} run ${SYSTEM_TESTS}/test_daemon.py
bash ${SYSTEM_TESTS}/test_polish_workchains.sh
verdi daemon stop

# tests for the testing infrastructure
pytest --cov aiida --verbose --noconftest ${SYSTEM_TESTS}/test_test_manager.py
pytest --cov aiida --verbose --noconftest ${SYSTEM_TESTS}/test_ipython_magics.py
pytest --cov aiida --verbose --noconftest ${SYSTEM_TESTS}/test_profile_manager.py
python ${SYSTEM_TESTS}/test_plugin_testcase.py  # uses custom unittest test runner

# Until the `${SYSTEM_TESTS}/pytest` tests are moved within `tests` we have to run them separately and pass in the path to the
# `conftest.py` explicitly, because otherwise it won't be able to find the fixtures it provides
AIIDA_TEST_PROFILE=test_$AIIDA_TEST_BACKEND pytest --cov aiida --verbose tests/conftest.py ${SYSTEM_TESTS}/pytest

# main aiida-core tests
AIIDA_TEST_PROFILE=test_$AIIDA_TEST_BACKEND pytest --cov aiida --verbose tests
