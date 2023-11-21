#!/bin/bash
RABBITMQ_DATA_DIR="/home/${SYSTEM_USER}/.rabbitmq"

mkdir -p "${RABBITMQ_DATA_DIR}"
fix-permissions "${RABBITMQ_DATA_DIR}"

# Fix issue where the erlang cookie permissions are corrupted.
chmod 400 "/home/${SYSTEM_USER}/.erlang.cookie" || echo "erlang cookie not created yet."

# Set base directory for RabbitMQ to persist its data. This needs to be set to a folder in the system user's home
# directory as that is the only folder that is persisted outside of the container.
RMQ_ETC_DIR="/opt/rabbitmq_server-${RMQ_VERSION}/etc/rabbitmq"
echo MNESIA_BASE="${RABBITMQ_DATA_DIR}" >> "${RMQ_ETC_DIR}/rabbitmq-env.conf"
echo LOG_BASE="${RABBITMQ_DATA_DIR}/log" >> "${RMQ_ETC_DIR}/rabbitmq-env.conf"

# using workaround from https://github.com/aiidateam/aiida-core/wiki/RabbitMQ-version-to-use
# setting the consumer_timeout to undefined disables the timeout
cat > "${RMQ_ETC_DIR}/advanced.config" <<EOF
%% advanced.config
[
  {rabbit, [
    {consumer_timeout, undefined}
  ]}
].
EOF

# Explicitly define the node name. This is necessary because the mnesia subdirectory contains the hostname, which by
# default is set to the value of $(hostname -s), which for docker containers, will be a random hexadecimal string. Upon
# restart, this will be different and so the original mnesia folder with the persisted data will not be found. The
# reason RabbitMQ is built this way is through this way it allows to run multiple nodes on a single machine each with
# isolated mnesia directories. Since in the AiiDA setup we only need and run a single node, we can simply use localhost.
echo NODENAME=rabbit@localhost >> "${RMQ_ETC_DIR}/rabbitmq-env.conf"
