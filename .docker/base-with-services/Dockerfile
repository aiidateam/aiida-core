# syntax=docker/dockerfile:1
FROM base

LABEL maintainer="AiiDAlab Team <aiidalab@materialscloud.org>"

USER root
WORKDIR /opt/

ARG PGSQL_VERSION
ARG RMQ_VERSION

ENV PGSQL_VERSION=${PGSQL_VERSION}
ENV RMQ_VERSION=${RMQ_VERSION}

RUN mamba create -p /opt/conda/envs/aiida-core-services --yes \
     --channel conda-forge \
     postgresql=${PGSQL_VERSION} && \
     mamba clean --all -f -y && \
     fix-permissions "${CONDA_DIR}" && \
     fix-permissions "/home/${NB_USER}"

# Install erlang.
RUN apt-get update --yes && \
     apt-get install --yes --no-install-recommends \
     erlang \
     xz-utils && \
     apt-get clean && rm -rf /var/lib/apt/lists/* && \
     # Install rabbitmq.
     wget -c --no-check-certificate https://github.com/rabbitmq/rabbitmq-server/releases/download/v${RMQ_VERSION}/rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     tar -xf rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     rm rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     mv rabbitmq_server-${RMQ_VERSION} /opt/conda/envs/aiida-core-services/ && \
     ln -sf /opt/conda/envs/aiida-core-services/rabbitmq_server-${RMQ_VERSION}/sbin/* /opt/conda/envs/aiida-core-services/bin/ && \
     fix-permissions "${CONDA_DIR}"

# s6-overlay to start services
COPY --chown="${SYSTEM_UID}:${SYSTEM_GID}" s6-assets/config-quick-setup.yaml "/aiida/assets/config-quick-setup.yaml"
COPY s6-assets/s6-rc.d /etc/s6-overlay/s6-rc.d
COPY s6-assets/init /etc/init

# Otherwise will stuck on oneshot services
# https://github.com/just-containers/s6-overlay/issues/467
ENV S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0

USER ${SYSTEM_UID}

WORKDIR "/home/${SYSTEM_USER}"
