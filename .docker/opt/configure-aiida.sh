#!/bin/bash

# This script is executed whenever the docker container is (re)started.

# Debugging.
set -x

# Environment.
export SHELL=/bin/bash

# Setup AiiDA autocompletion.
grep _VERDI_COMPLETE /home/${SYSTEM_USER}/.bashrc &> /dev/null || echo 'eval "$(_VERDI_COMPLETE=source verdi)"' >> /home/${SYSTEM_USER}/.bashrc

# Check if user requested to set up AiiDA profile (and if it exists already)
if [[ ${SETUP_DEFAULT_PROFILE} == true ]] && ! verdi profile show ${PROFILE_NAME} &> /dev/null; then
    NEED_SETUP_PROFILE=true;
else
    NEED_SETUP_PROFILE=false;
fi

# Setup AiiDA profile if needed.
if [[ ${NEED_SETUP_PROFILE} == true ]]; then

    # Create AiiDA profile.
    verdi quicksetup                           \
        --non-interactive                      \
        --profile "${PROFILE_NAME}"            \
        --email "${USER_EMAIL}"                \
        --first-name "${USER_FIRST_NAME}"      \
        --last-name "${USER_LAST_NAME}"        \
        --institution "${USER_INSTITUTION}"    \
        --db-backend "${AIIDADB_BACKEND}"

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

    verdi computer show ${computer_name} || verdi computer setup   \
        --non-interactive                                          \
        --label "${computer_name}"                                 \
        --description "this computer"                              \
        --hostname "${computer_name}"                              \
        --transport core.local                                          \
        --scheduler core.direct                                    \
        --work-dir /home/aiida/aiida_run/                          \
        --mpirun-command "mpirun -np {tot_num_mpiprocs}"           \
        --mpiprocs-per-machine ${LOCALHOST_MPI_PROCS_PER_MACHINE} && \
    verdi computer configure core.local "${computer_name}"              \
        --non-interactive                                          \
        --safe-interval 0.0
fi


# Show the default profile
verdi profile show || echo "The default profile is not set."

# Make sure that the daemon is not running, otherwise the migration will abort.
verdi daemon stop

# Migration will run for the default profile.
verdi storage migrate --force || echo "Database migration failed."

# Supress rabbitmq version warning for arm64 since
# the it build using latest version rabbitmq from apt install
# We explicitly set consumer_timeout to 100 hours in /etc/rabbitmq/rabbitmq.conf
export ARCH=`uname -m`
if [ "$ARCH" = "aarch64" ]; then \
    verdi config set warnings.rabbitmq_version False
fi


# Daemon will start only if the database exists and is migrated to the latest version.
verdi daemon start || echo "AiiDA daemon is not running."
