#!/bin/bash
# Read two integers from file 'aiida.in` and echo their sum

set -e 

x=$(cat aiida.in | awk '{print $1}')
y=$(cat aiida.in | awk '{print $2}')
echo $(( $x + $y ))
