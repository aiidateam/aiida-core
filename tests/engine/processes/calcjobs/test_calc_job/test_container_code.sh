#!/bin/bash
#SBATCH --no-requeue
#SBATCH --job-name="aiida-2"
#SBATCH --get-user-env
#SBATCH --output=_scheduler-stdout.txt
#SBATCH --error=_scheduler-stderr.txt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=128


'sarus' 'tmp_params' 'cscs/qe-mpich' '/usr/bin/pw.x'   
