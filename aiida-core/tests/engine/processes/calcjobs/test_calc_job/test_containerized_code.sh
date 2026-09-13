#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


"singularity" "exec" "--bind" "$PWD:$PWD" "ubuntu" '/bin/bash' '--version' '-c' < "aiida.in" > "aiida.out" 2> "aiida.err"
