#!/bin/bash

# make DB directory, if not existent
if [ ! -d /home/${SYSTEM_USER}/.postgresql ]; then
   mkdir /home/${SYSTEM_USER}/.postgresql
   initdb -D /home/${SYSTEM_USER}/.postgresql
   echo "unix_socket_directories = '/tmp'" >> /home/${SYSTEM_USER}/.postgresql/postgresql.conf
fi

PSQL_STATUS_CMD="pg_ctl -D /home/${SYSTEM_USER}/.postgresql status"

# Fix problem with kubernetes cluster that adds rws permissions to the group
# for more details see: https://github.com/materialscloud-org/aiidalab-z2jh-eosc/issues/5
chmod g-rwxs /home/${SYSTEM_USER}/.postgresql -R

# stores return value in $?
running=true
${PSQL_STATUS_CMD} > /dev/null 2>&1 || running=false

# Postgresql was probably not shutdown properly. Cleaning up the mess...
if ! $running ; then
   echo "" > /home/${SYSTEM_USER}/.postgresql/logfile # empty log files
   rm -vf /home/${SYSTEM_USER}/.postgresql/postmaster.pid
fi
