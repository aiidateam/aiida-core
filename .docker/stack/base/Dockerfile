ARG BASE
FROM ${BASE}

LABEL maintainer="AiiDAlab Team <aiidalab@materialscloud.org>"

ARG NEW_MAMBA_USER=aiida
ARG NEW_MAMBA_USER_ID=1000
ARG NEW_MAMBA_USER_GID=1000

USER root
RUN usermod "--login=${NEW_MAMBA_USER}" "--home=/home/${NEW_MAMBA_USER}" \
        --move-home "-u ${NEW_MAMBA_USER_ID}" "${MAMBA_USER}" && \
    groupmod "--new-name=${NEW_MAMBA_USER}" \
             "-g ${NEW_MAMBA_USER_GID}" "${MAMBA_USER}" && \
    # Update the expected value of MAMBA_USER for the
    # _entrypoint.sh consistency check.
    echo "${NEW_MAMBA_USER}" > "/etc/arg_mamba_user" && \
    :

ENV MAMBA_USER=$NEW_MAMBA_USER

# Pin python and pip version
ARG PYTHON_VERSION
ARG PIP_VERSION

# The docker only build after the release of conda-forge.
ARG AIIDA_VERSION

RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install the python base requirements to base environment.
# XXX: bring back mamba-bash-completion once it is available on conda-forge.
# https://github.com/conda-forge/mamba-bash-completion-feedstock/pull/2
RUN micromamba install --yes \
    --channel conda-forge \
    -n base \
    openssh \
    python=${PYTHON_VERSION} \
    pip=${PIP_VERSION} \
    aiida-core=${AIIDA_VERSION} \
    && micromamba clean --all -f -y

# Pin shared requirements in the base environemnt.
# XXX: ironup
RUN echo "pip==${PIP_VERSION}" >> /opt/requirements.txt
RUN echo "python==${PYTHON_VERSION}" >> /opt/requirements.txt
RUN echo "aiida-core==${AIIDA_VERSION}" >> /opt/requirements.txt

# Configure pip to use requirements file as constraints file.
ENV PIP_CONSTRAINT=/opt/requirements.txt

# copy the entrypoint script
COPY --chmod=755 init.d/* /usr/local/bin/init.d

# Enable verdi autocompletion.
RUN mkdir -p "/opt/conda/etc/conda/activate.d" && \
     echo 'eval "$(_VERDI_COMPLETE=bash_source verdi)"' >> "/opt/conda/etc/conda/activate.d/activate_aiida_autocompletion.sh" && \
     chmod +x "/opt/conda/etc/conda/activate.d/activate_aiida_autocompletion.sh"

# Install the load-singlesshagent.sh script as described here:
# https://aiida.readthedocs.io/projects/aiida-core/en/v2.0.0/howto/ssh.html#starting-the-ssh-agent
RUN wget --no-check-certificate --directory-prefix=/opt/conda/ \
     "https://aiida.readthedocs.io/projects/aiida-core/en/v2.0.0/_downloads/4265ec5a42c3a3dba586dd460c0db95e/load-singlesshagent.sh"

# SSH agent configuration

# Make sure that the known_hosts file is present inside the .ssh folder.
RUN mkdir -p --mode=0700 /home/${MAMBA_USER}/.ssh && \
        touch /home/${MAMBA_USER}/.ssh/known_hosts

RUN /usr/local/bin/_entrypoint.sh ssh-keygen -f /home/${MAMBA_USER}/.ssh/id_rsa -t rsa -b 4096 -m PEM -N ''

# Configure AiiDA profile.
COPY config-quick-setup.yaml /opt/config-quick-setup.yaml

# Environment variables for AiiDA profile setup
ENV SETUP_DEFAULT_AIIDA_PROFILE true
ENV AIIDA_PROFILE_NAME default
ENV AIIDA_USER_EMAIL aiida@localhost
ENV AIIDA_USER_FIRST_NAME Giuseppe
ENV AIIDA_USER_LAST_NAME Verdi
ENV AIIDA_USER_INSTITUTION Khedivial

# Switch to system user
USER $MAMBA_USER

WORKDIR /home/${MAMBA_USER}

ENTRYPOINT [ "/usr/local/bin/_init.sh" ]
