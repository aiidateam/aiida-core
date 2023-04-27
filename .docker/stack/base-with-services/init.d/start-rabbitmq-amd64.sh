#!/bin/bash
set -em

RABBITMQ_DATA_DIR="/home/${NB_USER}/.rabbitmq"

mkdir -p "${RABBITMQ_DATA_DIR}"
fix-permissions "${RABBITMQ_DATA_DIR}"

# Fix issue where the erlang cookie permissions are corrupted.
chmod 400 "/home/${NB_USER}/.erlang.cookie" || echo "erlang cookie not created yet."

# Set base directory for RabbitMQ to persist its data. This needs to be set to a folder in the system user's home
# directory as that is the only folder that is persisted outside of the container.
RMQ_ETC_DIR="/opt/conda/envs/aiida-core-services/etc/rabbitmq"
echo MNESIA_BASE="${RABBITMQ_DATA_DIR}" >> "${RMQ_ETC_DIR}/rabbitmq-env.conf"
echo LOG_BASE="${RABBITMQ_DATA_DIR}/log" >> "${RMQ_ETC_DIR}/rabbitmq-env.conf"

# Explicitly define the node name. This is necessary because the mnesia subdirectory contains the hostname, which by
# default is set to the value of $(hostname -s), which for docker containers, will be a random hexadecimal string. Upon
# restart, this will be different and so the original mnesia folder with the persisted data will not be found. The
# reason RabbitMQ is built this way is through this way it allows to run multiple nodes on a single machine each with
# isolated mnesia directories. Since in the AiiDA setup we only need and run a single node, we can simply use localhost.
echo NODENAME=rabbit@localhost >> "${RMQ_ETC_DIR}/rabbitmq-env.conf"

mamba run -n aiida-core-services rabbitmq-server -detached
