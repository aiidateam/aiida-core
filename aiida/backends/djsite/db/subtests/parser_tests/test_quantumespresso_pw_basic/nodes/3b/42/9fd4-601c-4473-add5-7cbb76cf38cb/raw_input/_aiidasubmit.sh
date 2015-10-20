#!/bin/bash

#SBATCH --no-requeue
#SBATCH --job-name="aiida-28266"
#SBATCH --get-user-env
#SBATCH --output=_scheduler-stdout.txt
#SBATCH --error=_scheduler-stderr.txt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16
#SBATCH --time=00:30:00


module load intelmpi/4.1.3

module load quantum-espresso/5.1.1/intel-15.0.0

'mpirun' '-np' '16' '/ssoft/quantum-espresso/5.1.1/RH6/intel-15.0.0/x86_E5v2/intel/pw.x' '-in' 'aiida.in'  > 'aiida.out' 
