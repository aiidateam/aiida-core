#!/bin/bash

# Be verbose, and stop with error as soon there's one
set -ev

if [[ "$TEST_TYPE" == "tests" ]]
then
    # start the daemon for the correct profile
    # (actually, for the way it works now, the -p probably does not
    #  have any effect...)
    verdi -p $TEST_AIIDA_BACKEND daemon start
    
    # Setup the torquessh computer
    cat ${TRAVIS_BUILD_DIR}/.travis-data/computer-setup-input.txt | verdi -p $TEST_AIIDA_BACKEND computer setup

    # Configure the torquessh computer
    cat ${TRAVIS_BUILD_DIR}/.travis-data/computer-configure-input.txt | verdi -p $TEST_AIIDA_BACKEND computer configure torquessh

    # Configure the 'doubler' code inside torquessh
    cat ${TRAVIS_BUILD_DIR}/.travis-data/code-setup-input.txt | verdi -p $TEST_AIIDA_BACKEND code setup

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
    
fi
