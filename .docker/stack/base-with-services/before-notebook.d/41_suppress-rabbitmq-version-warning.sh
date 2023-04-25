#!/bin/bash
set -em

# Supress rabbitmq version warning for arm64 since
# it is built using latest version rabbitmq from apt install.
# We explicitly set consumer_timeout to 100 hours in /etc/rabbitmq/rabbitmq.conf
verdi config set warnings.rabbitmq_version False
