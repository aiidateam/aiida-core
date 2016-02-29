#!/bin/bash

#PBS -r n
#PBS -m n
#PBS -N aiida-27369
#PBS -V
#PBS -o _scheduler-stdout.txt
#PBS -e _scheduler-stderr.txt
#PBS -l walltime=00:30:00
#PBS -l select=1:mpiprocs=6
cd "$PBS_O_WORKDIR"


'mpirun' '-np' '6' '/usr/bin/nwchem' 'aiida.in'  > 'aiida.out' 2> 'aiida.err'
