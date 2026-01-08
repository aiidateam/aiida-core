# syntax=docker/dockerfile:1

# Inspired by jupyter's docker-stacks-fundation image:
# https://github.com/jupyter/docker-stacks/tree/main/images/docker-stacks-foundation/Dockerfile

ARG BASE=ubuntu:22.04

FROM $BASE

LABEL maintainer="AiiDA Team <developers@aiida.net>"

ARG SYSTEM_USER="aiida"
ARG SYSTEM_UID="1000"
ARG SYSTEM_GID="100"


# Fix: https://github.com/hadolint/hadolint/wiki/DL4006
# Fix: https://github.com/koalaman/shellcheck/wiki/SC3014
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

ENV SYSTEM_USER="${SYSTEM_USER}"

# Install all OS dependencies for notebook server that starts but lacks all
# features (e.g., download as all possible file formats)
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update --yes && \
    # - apt-get upgrade is run to patch known vulnerabilities in apt-get packages as
    #   the ubuntu base image is rebuilt too seldom sometimes (less than once a month)
    apt-get upgrade --yes && \
    apt-get install --yes --no-install-recommends \
    # - bzip2 is necessary to extract the micromamba executable.
    bzip2 \
    # - xz-utils is necessary to extract the s6-overlay.
    xz-utils \
    ca-certificates \
    locales \
    sudo \
    # development tools
    git \
    openssh-client \
    rsync \
    graphviz \
    vim \
    # the gcc compiler need to build some python packages e.g. psutil and pymatgen
    build-essential \
    wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen

# Install s6-overlay to handle startup and shutdown of services
ARG S6_OVERLAY_VERSION=3.1.5.0
RUN wget --progress=dot:giga -O /tmp/s6-overlay-noarch.tar.xz \
        "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz && \
    rm /tmp/s6-overlay-noarch.tar.xz

RUN set -x && \
    arch=$(uname -m) && \
    wget --progress=dot:giga -O /tmp/s6-overlay-binary.tar.xz \
        "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${arch}.tar.xz" && \
    tar -C / -Jxpf /tmp/s6-overlay-binary.tar.xz && \
    rm /tmp/s6-overlay-binary.tar.xz

# Configure environment
ENV CONDA_DIR=/opt/conda \
    SHELL=/bin/bash \
    SYSTEM_USER="${SYSTEM_USER}" \
    SYSTEM_UID=${SYSTEM_UID} \
    SYSTEM_GID=${SYSTEM_GID} \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8
ENV PATH="${CONDA_DIR}/bin:${PATH}" \
    HOME="/home/${SYSTEM_USER}"


# Copy a script that we will use to correct permissions after running certain commands
COPY fix-permissions /usr/local/bin/fix-permissions
RUN chmod a+rx /usr/local/bin/fix-permissions

# Enable prompt color in the skeleton .bashrc before creating the default SYSTEM_USER
# hadolint ignore=SC2016
RUN sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc && \
   # Add call to conda init script see https://stackoverflow.com/a/58081608/4413446
   echo 'eval "$(command conda shell.bash hook 2> /dev/null)"' >> /etc/skel/.bashrc

# Create $SYSTEM_USER user with UID=1000 and 'users' group
# and make sure these dirs are writable by the `users` group.
RUN echo "auth requisite pam_deny.so" >> /etc/pam.d/su && \
    sed -i.bak -e 's/^%admin/#%admin/' /etc/sudoers && \
    sed -i.bak -e 's/^%sudo/#%sudo/' /etc/sudoers && \
    useradd -l -m -s /bin/bash -N -u "${SYSTEM_UID}" "${SYSTEM_USER}" && \
    mkdir -p "${CONDA_DIR}" && \
    chown "${SYSTEM_USER}:${SYSTEM_GID}" "${CONDA_DIR}" && \
    chmod g+w /etc/passwd && \
    fix-permissions "${HOME}" && \
    fix-permissions "${CONDA_DIR}"

USER ${SYSTEM_UID}

# Pin python version here
ARG PYTHON_VERSION

# Download and install Micromamba, and initialize Conda prefix.
#   <https://github.com/mamba-org/mamba#micromamba>
#   Similar projects using Micromamba:
#     - Micromamba-Docker: <https://github.com/mamba-org/micromamba-docker>
#     - repo2docker: <https://github.com/jupyterhub/repo2docker>
# Install Python, Mamba
# Cleanup temporary files and remove Micromamba
# Correct permissions
# Do all this in a single RUN command to avoid duplicating all of the
# files across image layers when the permissions change
COPY --chown="${SYSTEM_UID}:${SYSTEM_GID}" initial-condarc "${CONDA_DIR}/.condarc"
WORKDIR /tmp
RUN set -x && \
    arch=$(uname -m) && \
    if [ "${arch}" = "x86_64" ]; then \
        # Should be simpler, see <https://github.com/mamba-org/mamba/issues/1437>
        arch="64"; \
    fi && \
    wget --progress=dot:giga -O /tmp/micromamba.tar.bz2 \
        "https://micromamba.snakepit.net/api/micromamba/linux-${arch}/latest" && \
    tar -xvjf /tmp/micromamba.tar.bz2 --strip-components=1 bin/micromamba && \
    rm /tmp/micromamba.tar.bz2 && \
    PYTHON_SPECIFIER="python=${PYTHON_VERSION}" && \
    if [[ "${PYTHON_VERSION}" == "default" ]]; then PYTHON_SPECIFIER="python"; fi && \
    # Install the packages
    ./micromamba install \
        --root-prefix="${CONDA_DIR}" \
        --prefix="${CONDA_DIR}" \
        --yes \
        "${PYTHON_SPECIFIER}" \
        mamba=2.4 && \
    rm micromamba && \
    # Pin major.minor version of python
    mamba list python | grep -oP 'python\s+\K[\d.]+' | tr -s ' ' | cut -d ' ' -f 1,2 >> "${CONDA_DIR}/conda-meta/pinned" && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${SYSTEM_USER}"

# Add ~/.local/bin to PATH where the dependencies get installed via pip
# This require the package installed with `--user` flag in pip, which we set as default.
ENV PATH=${PATH}:/home/${SYSTEM_USER}/.local/bin
ENV PIP_USER=1

# Switch to root to install AiiDA and set AiiDA as service
# Install AiiDA from source code
USER root
COPY --from=src . /tmp/aiida-core
RUN pip install /tmp/aiida-core --no-cache-dir && \
    rm -rf /tmp/aiida-core

# Enable verdi autocompletion.
RUN mkdir -p "${CONDA_DIR}/etc/conda/activate.d" && \
     echo 'eval "$(_VERDI_COMPLETE=bash_source verdi)"' >> "${CONDA_DIR}/etc/conda/activate.d/activate_aiida_autocompletion.sh" && \
     chmod +x "${CONDA_DIR}/etc/conda/activate.d/activate_aiida_autocompletion.sh" && \
     fix-permissions "${CONDA_DIR}"

# COPY AiiDA profile configuration for profile setup init script
COPY s6-assets/s6-rc.d /etc/s6-overlay/s6-rc.d
COPY s6-assets/init /etc/init
RUN mkdir /etc/init/run-before-daemon-start && \
    mkdir /etc/init/run-after-daemon-start

# Otherwise will stuck on oneshot services
# https://github.com/just-containers/s6-overlay/issues/467
ENV S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0

# Switch back to USER aiida to avoid accidental container runs as root
USER ${SYSTEM_UID}

ENTRYPOINT ["/init"]

WORKDIR "${HOME}"
