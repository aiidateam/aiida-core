# syntax=docker/dockerfile:1
FROM base

LABEL maintainer="AiiDAlab Team <aiidalab@materialscloud.org>"

USER root
WORKDIR /opt/

ARG AIIDA_VERSION
ARG PGSQL_VERSION
ARG TARGETARCH

RUN mamba create -p /opt/conda/envs/aiida-core-services --yes \
     postgresql=${PGSQL_VERSION} \
     && mamba clean --all -f -y && \
     fix-permissions "${CONDA_DIR}" && \
     fix-permissions "/home/${NB_USER}"

# Install RabbitMQ in a dedicated conda environment.
# If the architecture is arm64, we install the default version of rabbitmq provided by the generic binary,
# # https://www.rabbitmq.com/install-generic-unix.html the version needs to be compatible with system's erlang version.
RUN if [ "$TARGETARCH" = "amd64" ]; then \
     mamba install -p /opt/conda/envs/aiida-core-services --yes \
          rabbitmq-server=3.8.14  && \
     mamba clean --all -f -y && \
     fix-permissions "${CONDA_DIR}" && \
     fix-permissions "/home/${NB_USER}"; \
elif [ "$TARGETARCH" = "arm64" ]; then \
     # Install erlang.
     apt-get update --yes && \
     apt-get install --yes --no-install-recommends erlang && \
     apt-get clean && rm -rf /var/lib/apt/lists/* && \
     # Install rabbitmq.
     export RMQ_VERSION=3.9.13 && \
     wget -c https://github.com/rabbitmq/rabbitmq-server/releases/download/v${RMQ_VERSION}/rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     tar -xf rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     rm rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     mv rabbitmq_server-${RMQ_VERSION} /opt/conda/envs/aiida-core-services/ && \
     fix-permissions "/opt/conda/envs/aiida-core-services/rabbitmq_server-${RMQ_VERSION}" && \
     ln -sf /opt/conda/envs/aiida-core-services/rabbitmq_server-${RMQ_VERSION}/sbin/* /opt/conda/envs/aiida-core-services/bin/; \
else \
   echo "Unknown architecture: ${TARGETARCH}."; \
fi

# Configure AiiDA profile.
COPY config-quick-setup.yaml .
COPY before-notebook.d/20_start-postgresql.sh /usr/local/bin/before-notebook.d/
COPY before-notebook.d/30_start-rabbitmq-${TARGETARCH}.sh /usr/local/bin/before-notebook.d/

# Supress rabbitmq version warning for arm64 since
# it is built using latest version rabbitmq from apt install.
# We explicitly set consumer_timeout to 100 hours in /etc/rabbitmq/rabbitmq.conf
COPY before-notebook.d/41_suppress-rabbitmq-version-warning.sh /usr/local/bin/before-notebook.d/
RUN if [ "$TARGETARCH" = "amd64" ]; then \
     rm /usr/local/bin/before-notebook.d/41_suppress-rabbitmq-version-warning.sh; \
fi

USER ${NB_USER}

WORKDIR "/home/${NB_USER}"

# Initialize the database
RUN mamba run -n aiida-core-services initdb -D aiida_db -U aiida
