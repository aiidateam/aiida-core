#!/bin/bash

set -ev

# Needed on Jenkins
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

coverage xml -o coverage.xml
# location set in the .coveragerc config file
coverage html
