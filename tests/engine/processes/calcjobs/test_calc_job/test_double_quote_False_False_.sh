#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


'mpirun' '-np' '1' '/bin/bash' < 'aiida.in' > 'aiida.out' 2> 'aiida.err'
