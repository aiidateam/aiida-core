#!/bin/bash

# Be verbose, and stop with error as soon there's one
set -ev

# The following is needed on jenkins, for some reason
# bashrc is not reloaded automatically
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

if [[ "$TEST_TYPE" == "tests" ]]
then
    # Add the .ci and the polish folder to the python path such that defined workchains can be found by the daemon
    export PYTHONPATH="${PYTHONPATH}:${TRAVIS_BUILD_DIR}/.ci"
    export PYTHONPATH="${PYTHONPATH}:${TRAVIS_BUILD_DIR}/.ci/polish"

    # Start the daemon for the correct profile and add four additional workers to prevent deadlock with integration tests
    verdi -p $TEST_AIIDA_BACKEND daemon start
    verdi -p $TEST_AIIDA_BACKEND daemon incr 4
    
    if [[ "$COMPUTER_SETUP_TYPE" != "jenkins" ]]
    then
        # Setup the torquessh computer
        cat ${TRAVIS_BUILD_DIR}/.ci/computer-torquessh-setup-input.txt | verdi -p $TEST_AIIDA_BACKEND computer setup

        # Configure the torquessh computer
        cat ${TRAVIS_BUILD_DIR}/.ci/computer-torquessh-configure-input.txt | verdi -p $TEST_AIIDA_BACKEND computer configure torquessh

        # Configure the 'doubler' code inside torquessh
        cat ${TRAVIS_BUILD_DIR}/.ci/code-doubler-setup-input.txt | verdi -p $TEST_AIIDA_BACKEND code setup

        # Make sure that the torquessh (localhost:10022) key is hashed
        # in the known_hosts file
        echo "'ssh-keyscan -p 10022 -t rsa localhost' output:"
        ssh-keyscan -p 10022 -t rsa localhost > /tmp/localhost10022key.txt
        cat /tmp/localhost10022key.txt

        # Patch for OpenSSH 6, that does not write the port number in the
        # known_hosts file. OpenSSH 7 would work, instead
        if grep -e '^localhost' /tmp/localhost10022key.txt > /dev/null 2>&1 ; then cat /tmp/localhost10022key.txt | sed 's/^localhost/[localhost]:10022/' >> ${HOME}/.ssh/known_hosts ; else  cat /tmp/localhost10022key.txt >> ${HOME}/.ssh/known_hosts; fi

        echo "Content of the known_hosts file:"
        cat ${HOME}/.ssh/known_hosts
    else
        # Computer configuration on Jenkins

        # Setup the torquessh computer - this one is custom, using direct scheduler
        cat .ci/computer-direct-setup-input.txt | verdi -p $TEST_AIIDA_BACKEND computer setup

        # Configure the torquessh computer - this one is custom, using port 22
        cat .ci/computer-direct-configure-input.txt | verdi -p $TEST_AIIDA_BACKEND computer configure torquessh

        # Configure the 'doubler' code inside torquessh
        cat .ci/code-doubler-setup-input.txt | verdi -p $TEST_AIIDA_BACKEND code setup

        # Configure the 'add' code inside torquessh, which is only required for the integrations test on Jenkins
        cat .ci/code-add-setup-input.txt | verdi -p $TEST_AIIDA_BACKEND code setup

        ## The key of localhost should be already set in the Jenkinsfile
    fi
fi
