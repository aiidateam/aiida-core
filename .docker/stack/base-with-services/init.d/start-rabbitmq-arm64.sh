#!/bin/bash
set -em

RABBITMQ_DATA_DIR="/home/${NB_USER}/.rabbitmq"

mkdir -p "${RABBITMQ_DATA_DIR}"
fix-permissions "${RABBITMQ_DATA_DIR}"

# Fix issue where the erlang cookie permissions are corrupted.
chmod 400 "/home/${NB_USER}/.erlang.cookie" || echo "erlang cookie not created yet."

# Set base directory for RabbitMQ to persist its data. This needs to be set to a folder in the system user's home
# directory as that is the only folder that is persisted outside of the container.
export RMQ_VERSION=3.9.13
RMQ_ETC_DIR="/opt/conda/envs/aiida-core-services/rabbitmq_server-${RMQ_VERSION}/etc/rabbitmq"
echo MNESIA_BASE="${RABBITMQ_DATA_DIR}" >> "${RMQ_ETC_DIR}/rabbitmq-env.conf"
echo LOG_BASE="${RABBITMQ_DATA_DIR}/log" >> "${RMQ_ETC_DIR}/rabbitmq-env.conf"

# RabbitMQ with versions >= 3.8.15 have reduced some default timeouts
# baseimage phusion/baseimage:jammy-1.0.0 running ubuntu 22.04 will install higher version of rabbimq by apt.
# using workaround from https://github.com/aiidateam/aiida-core/wiki/RabbitMQ-version-to-use
# set timeout to 100 hours
echo "consumer_timeout=3600000" >> "${RMQ_ETC_DIR}/rabbitmq.conf"

# Explicitly define the node name. This is necessary because the mnesia subdirectory contains the hostname, which by
# default is set to the value of $(hostname -s), which for docker containers, will be a random hexadecimal string. Upon
# restart, this will be different and so the original mnesia folder with the persisted data will not be found. The
# reason RabbitMQ is built this way is through this way it allows to run multiple nodes on a single machine each with
# isolated mnesia directories. Since in the AiiDA setup we only need and run a single node, we can simply use localhost.
echo NODENAME=rabbit@localhost >> "${RMQ_ETC_DIR}/rabbitmq-env.conf"

mamba run -n aiida-core-services rabbitmq-server -detached
