#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


"mpirun" "-np" "1" "singularity" "exec" "--bind" "$PWD:$PWD" "ubuntu" '/bin/bash' '--version' '-c' < "aiida.in" > "aiida.out" 2> "aiida.err"
