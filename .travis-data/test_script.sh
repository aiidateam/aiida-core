#!/bin/bash

# Be verbose, and stop with error as soon there's one
set -ev

case "$TEST_TYPE" in
    docs)
        # Compile the docs (HTML format); -W to convert warnings in errors,
        # -n to warn about all missing references
        SPHINXOPTS="-nW" make -C docs html
        ;;
    tests)
        # Add the .travis-data folder to the python path such that defined workchains can be found by the daemon
        export PYTHONPATH=${PYTHONPATH}:${TRAVIS_BUILD_DIR}/.travis-data

        # Run the AiiDA tests
        python ${TRAVIS_BUILD_DIR}/.travis-data/test_setup.py
        python ${TRAVIS_BUILD_DIR}/.travis-data/test_fixtures.py
        python ${TRAVIS_BUILD_DIR}/.travis-data/test_plugin_testcase.py

        verdi -p test_$TEST_AIIDA_BACKEND devel tests

        # Run the daemon tests using docker
        verdi -p $TEST_AIIDA_BACKEND run ${TRAVIS_BUILD_DIR}/.travis-data/test_daemon.py
        ;;
    pre-commit)
        pre-commit run --all-files || ( git status --short ; git diff ; exit 1 )
        ;;
    sphinxext)
        py.test -vv aiida/sphinxext/tests
        ;;
esac
