#!/bin/bash

# This script is executed whenever the docker container is (re)started.

# Environment.
export SHELL=/bin/bash

# Configure AiiDA.
export SETUP_DEFAULT_AIIDA_PROFILE=true
export AIIDA_PROFILE_NAME=default
export AIIDA_USER_EMAIL=aiida@localhost
export AIIDA_USER_FIRST_NAME=Giuseppe
export AIIDA_USER_LAST_NAME=Verdi
export AIIDA_USER_INSTITUTION=Khedivial
export AIIDA_PROFILE_PATH=/aiida/assets/config-quick-setup.yaml

# Check if user requested to set up AiiDA profile (and if it exists already)
if [[ ${SETUP_DEFAULT_AIIDA_PROFILE} == true ]] && ! verdi profile show ${AIIDA_PROFILE_NAME} &> /dev/null; then
    NEED_SETUP_PROFILE=true;
else
    NEED_SETUP_PROFILE=false;
fi

# Setup AiiDA profile if needed.
if [[ ${NEED_SETUP_PROFILE} == true ]]; then

    # Create AiiDA profile.
    verdi quicksetup              \
        --non-interactive                            \
        --profile "${AIIDA_PROFILE_NAME}"            \
        --email "${AIIDA_USER_EMAIL}"                \
        --first-name "${AIIDA_USER_FIRST_NAME}"      \
        --last-name "${AIIDA_USER_LAST_NAME}"        \
        --institution "${AIIDA_USER_INSTITUTION}"    \
        --config "${AIIDA_PROFILE_PATH}"

    # Supress verdi version warning because we are using a development version
    verdi config set warnings.development_version False

    # Supress rabbitmq version warning
    # If it is built using RMQ version > 3.8.15 (as we did for the `aiida-core` image) which has the issue as described in
    # https://github.com/aiidateam/aiida-core/wiki/RabbitMQ-version-to-use
    # We explicitly set consumer_timeout to 100 hours in /etc/rabbitmq/rabbitmq.conf
    verdi config set warnings.rabbitmq_version False

    # Setup and configure local computer.
    computer_name=localhost

    # Determine the number of physical cores as a default for the number of
    # available MPI ranks on the localhost. We do not count "logical" cores,
    # since MPI parallelization over hyper-threaded cores is typically
    # associated with a significant performance penalty. We use the
    # `psutil.cpu_count(logical=False)` function as opposed to simply
    # `os.cpu_count()` since the latter would include hyperthreaded (logical
    # cores).
    NUM_PHYSICAL_CORES=$(python -c 'import psutil; print(int(psutil.cpu_count(logical=False)))' 2>/dev/null)
    LOCALHOST_MPI_PROCS_PER_MACHINE=${LOCALHOST_MPI_PROCS_PER_MACHINE:-${NUM_PHYSICAL_CORES}}

    if [ -z $LOCALHOST_MPI_PROCS_PER_MACHINE ]; then
      echo "Unable to automatically determine the number of logical CPUs on this "
      echo "machine. Please set the LOCALHOST_MPI_PROCS_PER_MACHINE variable to "
      echo "explicitly set the number of available MPI ranks."
      exit 1
    fi

    verdi computer show ${computer_name} &> /dev/null || verdi computer setup \
        --non-interactive                                               \
        --label "${computer_name}"                                      \
        --description "container computer"                                   \
        --hostname "${computer_name}"                                   \
        --transport core.local                                          \
        --scheduler core.direct                                         \
        --work-dir /home/${SYSTEM_USER}/aiida_run/                          \
        --mpirun-command "mpirun -np {tot_num_mpiprocs}"                \
        --mpiprocs-per-machine ${LOCALHOST_MPI_PROCS_PER_MACHINE} &&    \
    verdi computer configure core.local "${computer_name}" \
        --non-interactive                                               \
        --safe-interval 0.0
fi


# Show the default profile
verdi profile show || echo "The default profile is not set."

# Migration will run for the default profile.
verdi storage migrate --force
