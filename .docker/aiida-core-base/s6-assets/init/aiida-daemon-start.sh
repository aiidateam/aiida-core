#!/bin/bash

verdi profile show
if [ $? == 0 ]; then
    # Start the daemon
    verdi daemon start
else
    echo "The default profile is not set."
fi
