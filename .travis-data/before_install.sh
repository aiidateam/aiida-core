#!/bin/bash

# Be verbose, and stop with error as soon there's one
set -ev

if [[ "$TEST_TYPE" == "tests" ]]
then
    THEKEY=`ssh-keygen -y -f "${HOME}/.ssh/id_rsa"`
    echo 'AUTHORIZED_KEY='"$THEKEY" > "${TRAVIS_BUILD_DIR}/torquessh.env"
    docker build -t torquessh "${TRAVIS_BUILD_DIR}/.travis-data/torquessh-doubler"
    # Run it in the background, mapping port 22 of the container
    # to port 10022 outside, and passing the environment variable
    docker run -d --privileged -p=10022:22 --env-file "${TRAVIS_BUILD_DIR}/torquessh.env" torquessh
    # Docker ps to see what is going on
    echo "Running docker ps to see if the 'torquessh' docker image is up..."
    docker ps    
    # Wait for SSH to be up
    "${TRAVIS_BUILD_DIR}"/.travis-data/wait-for-it.sh localhost:10022 -t 0

    # I will add the key to the known_hosts later, to give the time to ssh
    # to be really up - see the before_script script
    #ssh-keyscan -p 10022 localhost >> ${HOME}/.ssh/known_hosts
    
fi
