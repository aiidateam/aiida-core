#!/bin/bash

verdi profile show
if [ $? == 0 ]; then

    # Supress rabbitmq version warning
    # If it is built using RMQ version > 3.8.15 (as we did for the `aiida-core-with-services` image) which has the issue as described in
    # https://github.com/aiidateam/aiida-core/wiki/RabbitMQ-version-to-use
    # We explicitly set consumer_timeout to disabled in /etc/rabbitmq/rabbitmq.conf
    verdi config set warnings.rabbitmq_version False

    # Start the daemon
    verdi daemon start
else
    echo "The default profile is not set."
fi
