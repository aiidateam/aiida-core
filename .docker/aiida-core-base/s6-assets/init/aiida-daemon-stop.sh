#!/bin/bash

verdi profile show
if [ $? == 0 ]; then
    # Stop the daemon
    verdi daemon stop
fi
