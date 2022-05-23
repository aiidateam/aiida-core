#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


"docker" "run" "-it" "-v" "$PWD:/workdir:rw" "-w" "/workdir" "ubuntu" "sh" "-c" "'bash' < "'"'"aiida.in"'"'" > "'"'"aiida.out"'"'" "
