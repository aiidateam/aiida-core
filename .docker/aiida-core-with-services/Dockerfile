# syntax=docker/dockerfile:1
FROM aiida-core-base

LABEL maintainer="AiiDA Team <developers@aiida.net>"

USER root
WORKDIR /opt/

ARG PGSQL_VERSION
ARG RMQ_VERSION

ENV PGSQL_VERSION=${PGSQL_VERSION}
ENV RMQ_VERSION=${RMQ_VERSION}

RUN mamba install --yes \
     --channel conda-forge \
     postgresql=${PGSQL_VERSION} && \
     mamba clean --all -f -y && \
     fix-permissions "${CONDA_DIR}" && \
     fix-permissions "/home/${SYSTEM_USER}"

# Install erlang.
RUN apt-get update --yes && \
     apt-get install --yes --no-install-recommends \
     erlang && \
     apt-get clean && rm -rf /var/lib/apt/lists/* && \
     # Install rabbitmq.
     wget -c --no-check-certificate https://github.com/rabbitmq/rabbitmq-server/releases/download/v${RMQ_VERSION}/rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     tar -xf rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     rm rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     ln -sf /opt/rabbitmq_server-${RMQ_VERSION}/sbin/* /usr/local/bin/ && \
     fix-permissions /opt/rabbitmq_server-${RMQ_VERSION}

# s6-overlay to start services
COPY s6-assets/s6-rc.d /etc/s6-overlay/s6-rc.d
COPY s6-assets/init /etc/init

USER ${SYSTEM_UID}

WORKDIR "/home/${SYSTEM_USER}"
