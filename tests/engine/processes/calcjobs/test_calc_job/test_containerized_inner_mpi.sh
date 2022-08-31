#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


"conda" "run" "--name" "myenv" 'inner_mpirun' '-np' '1' '/bin/bash' '--version' '-c' < "aiida.in" > "aiida.out" 2> "aiida.err"
