#!/bin/bash

# Activate the conda environment with PostgreSQL installed in it.
# conda activate pgsql

# -w waits until server is up
SYSTEM_USER=${MAMBA_USER}
PSQL_START_CMD="pg_ctl --timeout=180 -w -D /home/${SYSTEM_USER}/.postgresql -l /home/${SYSTEM_USER}/.postgresql/logfile start"
PSQL_STOP_CMD="pg_ctl -w -D /home/${SYSTEM_USER}/.postgresql stop"
PSQL_STATUS_CMD="pg_ctl -D /home/${SYSTEM_USER}/.postgresql status"

MAMBA_RUN="micromamba run -n aiida-core-services"

# make DB directory, if not existent
if [ ! -d /home/${SYSTEM_USER}/.postgresql ]; then
   mkdir /home/${SYSTEM_USER}/.postgresql
   ${MAMBA_RUN} initdb -D /home/${SYSTEM_USER}/.postgresql
   echo "unix_socket_directories = '/tmp'" >> /home/${SYSTEM_USER}/.postgresql/postgresql.conf
   ${MAMBA_RUN} ${PSQL_START_CMD}

# else don't
else
    # Fix problem with kubernetes cluster that adds rws permissions to the group
    # for more details see: https://github.com/materialscloud-org/aiidalab-z2jh-eosc/issues/5
    chmod g-rwxs /home/${NBSYSTEM_USER_USER}/.postgresql -R

    # stores return value in $?
    running=true
    ${MAMBA_RUN} ${PSQL_STATUS_CMD} || running=false

    # Postgresql was probably not shutdown properly. Cleaning up the mess...
    if ! $running ; then
       echo "" > /home/${SYSTEM_USER}/.postgresql/logfile # empty log files
       rm -vf /home/${SYSTEM_USER}/.postgresql/postmaster.pid
       ${MAMBA_RUN} ${PSQL_START_CMD}
   fi
fi
