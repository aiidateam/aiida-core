#!/bin/bash
# Read cmdline parameter and sleep that number of seconds (or zero if not present)
# Then read integer from file 'value_to_double.txt`, multiply by two and echo that value

set -e

if [ "$1" != "" ]
then
    sleep $1
fi

INPUTVALUE=`cat value_to_double.txt`
echo $(( $INPUTVALUE * 2 ))
echo $(( $INPUTVALUE * 3 )) > 'triple_value.tmp'
