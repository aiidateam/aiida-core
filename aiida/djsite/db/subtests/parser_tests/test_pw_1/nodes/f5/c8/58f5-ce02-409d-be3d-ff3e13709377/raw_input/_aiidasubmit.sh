#!/bin/bash

#SBATCH --no-requeue
#SBATCH --job-name="aiida-161533"
#SBATCH --get-user-env
#SBATCH --output=_scheduler-stdout.txt
#SBATCH --error=_scheduler-stderr.txt
#SBATCH --nodes=8
#SBATCH --ntasks-per-node=24
#SBATCH --time=07:00:00
#SBATCH -A, --account=mr0


'aprun' '-n' '192' '/store/marvel/mr0/Nicolas/espresso-5.1.2_ntyp50/bin/pw.x' '-nk' '8' '-in' 'aiida.in'  > 'aiida.out' 
