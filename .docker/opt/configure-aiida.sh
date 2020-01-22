#!/bin/bash -e

# This script is executed whenever the docker container is (re)started.

#===============================================================================
# debugging
set -x

#===============================================================================
# environment
reentry scan

export SHELL=/bin/bash

#===============================================================================
# setup AiiDA
aiida_backend=django

if [ ! -d /home/$SYSTEM_USER/.aiida ]; then
    verdi setup                                \
        --profile default                      \
        --non-interactive                      \
        --email some.body@xyz.com              \
        --first-name Some                      \
        --last-name Body                       \
        --institution XYZ                      \
        --db-backend $aiida_backend            \
        --db-username aiida                    \
        --db-password aiida_db_passwd          \
        --db-name aiidadb                      \
        --db-host localhost                    \
        --db-port 5432                         \
        --repository /home/$SYSTEM_USER/aiida_repository

   echo 'eval "$(verdi completioncommand)"' >> /home/$SYSTEM_USER/.bashrc

   verdi profile setdefault default
fi

#===============================================================================
# perform the database migration if needed
#
verdi daemon start || ( verdi daemon stop && verdi database migrate --force && verdi daemon start)


#===============================================================================
# setup local computer

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

#EOF

