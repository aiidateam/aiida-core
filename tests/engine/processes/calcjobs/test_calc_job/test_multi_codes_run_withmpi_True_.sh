#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


'/bin/bash'   

'mpirun' '-np' '1' '/bin/bash'   
