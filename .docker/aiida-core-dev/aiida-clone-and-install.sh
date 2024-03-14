#!/bin/bash

REPO_PATH=/home/aiida/aiida-core

cp -R /opt/aiida-core $REPO_PATH

pip install --user -e "$REPO_PATH/[pre-commit,atomic_tools,docs,rest,tests,tui]" tox
