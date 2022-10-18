#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


"singularity" "exec" "--bind" "$PWD:$PWD" "ubuntu" 'bash' < "aiida.in" > "aiida.out" 
