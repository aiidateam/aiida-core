#!/usr/bin/env bash
set -ev

# Make sure the folder containing the workchains is in the python path before the daemon is started
SYSTEM_TESTS="${GITHUB_WORKSPACE}/.github/system_tests"

# Until the `${SYSTEM_TESTS}/pytest` tests are moved within `tests` we have to run them separately and pass in the path to the
# `conftest.py` explicitly, because otherwise it won't be able to find the fixtures it provides
AIIDA_TEST_PROFILE=test_aiida pytest --cov aiida --verbose tests/conftest.py ${SYSTEM_TESTS}/pytest

# main aiida-core tests
AIIDA_TEST_PROFILE=test_aiida pytest --cov aiida --verbose tests -m 'not nightly'
