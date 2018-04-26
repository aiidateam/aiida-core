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
        DATA_DIR=${TRAVIS_BUILD_DIR}/.travis-data
        # Add the .travis-data folder to the python path such that defined workchains can be found by the daemon
        export PYTHONPATH=${PYTHONPATH}:${DATA_DIR}

        # Run preliminary tests
        coverage run -a ${DATA_DIR}/test_setup.py
        coverage run -a ${DATA_DIR}/test_fixtures.py
        coverage run -a ${DATA_DIR}/test_plugin_testcase.py

        # Run verdi devel tests
        VERDI=`which verdi`
        coverage run -a $VERDI -p test_${TEST_AIIDA_BACKEND} devel tests

        # Run the daemon tests using docker
        # Note: This is not a typo, the profile is called ${TEST_AIIDA_BACKEND}

        # In case of error, I do some debugging, but I make sure I anyway exit with an exit error
        coverage run -a $VERDI -p ${TEST_AIIDA_BACKEND} run ${DATA_DIR}/test_daemon.py || ( if which docker > /dev/null ; then docker ps -a ; docker exec torquesshmachine cat /var/log/syslog ; fi ; exit 1 )

        # run the sphinxext tests
        pytest --cov aiida --cov-append -vv aiida/sphinxext/tests
        ;;
    pre-commit)
        pre-commit run --all-files || ( git status --short ; git diff ; exit 1 )
        ;;
esac
