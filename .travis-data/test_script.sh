#!/bin/bash

# Be verbose, and stop with error as soon there's one
set -ev

if [[ "$COMPILE_DOCS" == "true" ]]
then
    # Compile the docs (HTML format); -W to convert warnings in errors, 
    # -n to warn about all missing references
    SPHINXOPTS="-nW" make -C docs html
else
    # Run the AiiDA tests
    verdi -p test_$TEST_AIIDA_BACKEND devel tests

    # Run the daemon tests using docker
    verdi -p $TEST_AIIDA_BACKEND run ${TRAVIS_BUILD_DIR}/.travis-data/test_daemon.py
fi



