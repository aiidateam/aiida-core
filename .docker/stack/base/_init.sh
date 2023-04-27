#!/bin/bash

# This is the entrypoint script for the docker container.

# Start the ssh-agent
/usr/local/bin/_entrypoint.sh ssh-agent

# setup aiida must be run in the environment
/usr/local/bin/_entrypoint.sh /usr/local/bin/init.d/aiida-profile-preparation.sh

exec "$@"
