#!/bin/bash
exec > _scheduler-stdout.txt
exec 2> _scheduler-stderr.txt


"/bin/bash" < 'aiida.in' > 'aiida.out' 2> 'aiida.err'
