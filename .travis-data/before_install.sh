#!/bin/bash

# Be verbose, and stop with error as soon there's one
set -ev

if [ "$COMPILE_DOCS" == "false" ]
then
    THEKEY=`cat ${HOME}/.ssh/id_rsa.pub`
    echo 'AUTHORIZED_KEY='"$THEKEY" > ${HOME}/torquessh.env
    docker build -t torquessh ${HOME}/.travis-data/torquessh-doubler
    # Run it in the background, mapping port 22 of the container
    # to port 10022 outside, and passing the environment variable
    docker run -d --privileged -p=10022:22 --env-file ${HOME}/torquessh.env torquessh
    # Docker ps to see what is going on
    echo "Running docker ps to see if the 'torquessh' docker image is up..."
    docker ps    
    # Wait for SSH to be up
    ${HOME}/.travis-data/wait-for-it.sh localhost:10022 -t 0

    # Add the key to the known_hosts
    ssh-keyscan -p 10022 localhost >> ${HOME}/.ssh/known_hosts
    
fi
