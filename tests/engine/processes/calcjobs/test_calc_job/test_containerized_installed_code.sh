#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


"docker" "run" "-it" "-v" "$PWD:/workdir:rw" "-w" "/workdir" "ubuntu" "sh" "-c" "'/bin/bash' '--version' '-c' < "'"'"aiida.in"'"'" > "'"'"aiida.out"'"'" 2> "'"'"aiida.err"'"'""
