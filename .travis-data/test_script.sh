#!/bin/bash

# Be verbose, and stop with error as soon there's one
set -ev

# Needed on Jenkins
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

case "$TEST_TYPE" in
    docs)
        # Compile the docs (HTML format);
        # -C change to 'docs' directory before doing anything
        # -n to warn about all missing references
        # -W to convert warnings in errors
        SPHINXOPTS="-nW" make -C docs
        ;;
    tests)
        TRAVIS_DATA_DIR="${TRAVIS_BUILD_DIR}/.travis-data"
        JENKINS_DATA_DIR="${TRAVIS_BUILD_DIR}/.jenkins-data"

        # Add the .travis-data and .jenkins-data folder to the python path so workchains within it can be found by the daemon
        export PYTHONPATH="${PYTHONPATH}:${TRAVIS_DATA_DIR}"
        export PYTHONPATH="${PYTHONPATH}:${JENKINS_DATA_DIR}"

        # Clean up coverage file (there shouldn't be any, but just in case)
        coverage erase

        # Run preliminary tests
        coverage run -a "${TRAVIS_DATA_DIR}/test_setup.py"
        coverage run -a "${TRAVIS_DATA_DIR}/test_fixtures.py"
        coverage run -a "${TRAVIS_DATA_DIR}/test_plugin_testcase.py"

        # Run verdi devel tests
        VERDI=`which verdi`
        coverage run -a $VERDI -p test_${TEST_AIIDA_BACKEND} devel tests

        # Run the daemon tests using docker
        # Note: This is not a typo, the profile is called ${TEST_AIIDA_BACKEND}

        # In case of error, I do some debugging, but I make sure I anyway exit with an exit error
        coverage run -a $VERDI -p ${TEST_AIIDA_BACKEND} run "${TRAVIS_DATA_DIR}/test_daemon.py" || ( if which docker > /dev/null ; then docker ps -a ; docker exec torquesshmachine cat /var/log/syslog ; fi ; exit 1 )

        # Run the sphinxext tests, append to coverage file, do not create final report
        pytest --cov aiida --cov-append --cov-report= -vv aiida/sphinxext/tests

        # Now, we run all the tests and we manually create the final report
        # Note that this is only the partial coverage for this backend
        coverage report
        ;;
    pre-commit)
        pre-commit run --all-files || ( git status --short ; git diff ; exit 1 )
        ;;
esac
