#!/bin/bash

# Be verbose, and stop with error as soon there's one
set -ev

if [[ "$COMPILE_DOCS" == "false" ]]
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
    ssh-keyscan -p 10022 localhost >> ${HOME}/.ssh/known_hosts
    
fi



