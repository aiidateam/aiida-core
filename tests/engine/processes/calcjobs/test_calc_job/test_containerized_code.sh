#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


'docker' 'run' 'cscs/qe-mpich:latest' '/usr/bin/pw.x' < 'aiida.in' > 'aiida.out' 2> 'aiida.err'
