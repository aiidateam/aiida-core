#!/bin/bash

# This is the entrypoint script for the docker container.

# Start the ssh-agent
/usr/local/bin/_entrypoint.sh ssh-agent

# Start postgresql
# /usr/local/bin/_entrypoint.sh /usr/local/bin/init.d/start-postgres.sh

# Start rabbitmq
/usr/local/bin/_entrypoint.sh /usr/local/bin/init.d/start-rabbitmq.sh

# setup aiida must be run in the environment
/usr/local/bin/_entrypoint.sh /usr/local/bin/init.d/aiida-profile-preparation.sh

# supress the warning of incorrect rabbitmq version
/usr/local/bin/_entrypoint.sh /usr/local/bin/init.d/suppress-rabbitmq-version-warning.sh

exec "$@"
