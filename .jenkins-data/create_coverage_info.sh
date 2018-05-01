#!/bin/bash

set -e

# Needed on Jenkins
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

# Collect all coverage files of different backends, see
# http://coverage.readthedocs.io/en/latest/cmd.html#combining-data-files
coverage combine

# Create XML file
# coverage xml -o coverage.xml

# Create HTML file(s)
# location set in the .coveragerc config file
# coverage html

# Create text report
coverage report
