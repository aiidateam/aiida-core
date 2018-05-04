#!/usr/bin/env bash

# Be verbose, and stop with error as soon there's one
set -ev

# Needed on Jenkins
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

NUMBER_WORKCHAINS=5
CODE='add@torquessh'

for i in $(seq 1 $NUMBER_WORKCHAINS); do

    coverage run -a $(which verdi) -p ${TEST_AIIDA_BACKEND} run polish/cli.py -c $CODE -C -W -d -t 100

done