#!/bin/bash

#PBS -r n
#PBS -m n
#PBS -N aiida-3576
#PBS -V
#PBS -o _scheduler-stdout.txt
#PBS -e _scheduler-stderr.txt
#PBS -l walltime=00:30:00
#PBS -l select=1:mpiprocs=8
cd "$PBS_O_WORKDIR"


'mpirun' '-np' '6' '/home/gibertini/svn/espresso-most-recent/bin/neb.x' '-input_images' '2'  > 'aiida.out' 
