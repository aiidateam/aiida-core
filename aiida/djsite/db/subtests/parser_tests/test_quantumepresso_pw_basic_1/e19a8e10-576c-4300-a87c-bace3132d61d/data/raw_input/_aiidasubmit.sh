#!/bin/bash

#SBATCH --no-requeue
#SBATCH --job-name="aiida-591"
#SBATCH --get-user-env
#SBATCH --output=_scheduler-stdout.txt
#SBATCH --error=_scheduler-stderr.txt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --time=00:30:00


'aprun' '-n' '8' '/project/s337/espresso-svn-daint/bin/pw.x' < 'aiida.in' > 'aiida.out' 
