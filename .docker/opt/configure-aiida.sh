#!/bin/bash

# This script is executed whenever the docker container is (re)started.

# Debugging.
#set -x

# Environment.
reentry scan
export SHELL=/bin/bash

# Setup AiiDA autocompletion.
grep _VERDI_COMPLETE .bash_profile &> /dev/null || echo 'eval "$(_VERDI_COMPLETE=source verdi)"' >> /home/$SYSTEM_USER/.bashrc

# Check if profile $PROFILE_NAME needs to be setup an if it exists already
if [[ $SETUP_DEFAULT_PROFILE == true ]] && ! verdi profile show $PROFILE_NAME &> /dev/null; then
    NEED_SETUP_PROFILE=true;
else
    NEED_SETUP_PROFILE=false;
fi

# Setup AiiDA.
if [[ $NEED_SETUP_PROFILE == true ]]; then

    # Create postgres database first.
    psql -h localhost -d template1 -c "CREATE USER $AIIDADB_USER WITH PASSWORD '$AIIDADB_PASS';"
    psql -h localhost -d template1 -c "CREATE DATABASE $AIIDADB_NAME OWNER $AIIDADB_USER;"
    psql -h localhost -d template1 -c "GRANT ALL PRIVILEGES ON DATABASE $AIIDADB_NAME to $AIIDADB_USER;"

    # Then create AiiDA profile.
    verdi setup                                \
        --profile $PROFILE_NAME                \
        --non-interactive                      \
        --email $USER_EMAIL                    \
        --first-name $USER_FIRST_NAME          \
        --last-name $USER_LAST_NAME            \
        --institution $USER_INSTITUTION        \
        --db-backend $AIIDADB_BACKEND          \
        --db-username $AIIDADB_USER            \
        --db-password $AIIDADB_PASS            \
        --db-name $AIIDADB_NAME                \
        --db-host $AIIDADB_HOST                \
        --db-port $AIIDADB_PORT                \

    verdi profile setdefault $PROFILE_NAME

    # Finally setup and configure local computer.
    computer_name=localhost
    verdi computer show $computer_name || verdi computer setup \
        --non-interactive                                      \
        --label ${computer_name}                               \
        --description "this computer"                          \
        --hostname ${computer_name}                            \
        --transport local                                      \
        --scheduler direct                                     \
        --work-dir /home/aiida/aiida_run/                      \
        --mpirun-command "mpirun -np {tot_num_mpiprocs}"       \
        --mpiprocs-per-machine 1 &&                            \
    verdi computer configure local ${computer_name}            \
        --non-interactive                                      \
    --safe-interval 0.0
fi


# Perform the database migration if needed and start the daemon.
verdi database migrate --force

# Start AiiDA daemon.
verdi daemon start
