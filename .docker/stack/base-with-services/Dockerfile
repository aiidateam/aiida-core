# syntax=docker/dockerfile:1
FROM base

LABEL maintainer="AiiDAlab Team <aiidalab@materialscloud.org>"

USER root
WORKDIR /opt/

ARG AIIDA_VERSION
ARG PGSQL_VERSION
ARG TARGETARCH

RUN micromamba create -p /opt/conda/envs/aiida-core-services --yes \
     --channel conda-forge \
     postgresql=${PGSQL_VERSION} \
     && micromamba clean --all -f -y

# Install RabbitMQ in a dedicated conda environment.
# If the architecture is arm64, we install the default version of rabbitmq provided by the generic binary,
# # https://www.rabbitmq.com/install-generic-unix.html the version needs to be compatible with system's erlang version.
RUN if [ "$TARGETARCH" = "amd64" ]; then \
     micromamba install -p /opt/conda/envs/aiida-core-services --yes \
          --channel conda-forge \
          rabbitmq-server=3.8.14  && \
     micromamba clean --all -f -y; \
elif [ "$TARGETARCH" = "arm64" ]; then \
     # Install erlang.
     apt-get update --yes && \
     apt-get install --yes --no-install-recommends \
     erlang \
     xz-utils && \
     apt-get clean && rm -rf /var/lib/apt/lists/* && \
     # Install rabbitmq.
     export RMQ_VERSION=3.9.13 && \
     wget -c --no-check-certificate https://github.com/rabbitmq/rabbitmq-server/releases/download/v${RMQ_VERSION}/rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     tar -xf rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     rm rabbitmq-server-generic-unix-${RMQ_VERSION}.tar.xz && \
     mv rabbitmq_server-${RMQ_VERSION} /opt/conda/envs/aiida-core-services/ && \
     ln -sf /opt/conda/envs/aiida-core-services/rabbitmq_server-${RMQ_VERSION}/sbin/* /opt/conda/envs/aiida-core-services/bin/; \
else \
   echo "Unknown architecture: ${TARGETARCH}."; \
fi

# Configure AiiDA profile.
COPY config-quick-setup.yaml .
COPY --chmod=755 init.d/start-postgres.sh /usr/local/bin/init.d/
COPY --chmod=755 init.d/start-rabbitmq-${TARGETARCH}.sh /usr/local/bin/init.d/start-rabbitmq.sh
COPY --chmod=755 _init.sh /usr/local/bin/_init.sh

# Supress rabbitmq version warning for arm64 since
# it is built using latest version rabbitmq from apt install.
# We explicitly set consumer_timeout to 100 hours in /etc/rabbitmq/rabbitmq.conf
RUN if [ "$TARGETARCH" = "amd64" ]; then \
     rm /usr/local/bin/init.d/suppress-rabbitmq-version-warning.sh; \
fi

USER $MAMBA_USER

WORKDIR "/home/${MAMBA_USER}"

# Initialize the database
RUN micromamba run -n aiida-core-services initdb -D aiida_db -U aiida

ENTRYPOINT [ "/usr/local/bin/_init.sh" ]
# ENTRYPOINT ["_entrypoint.sh"]
