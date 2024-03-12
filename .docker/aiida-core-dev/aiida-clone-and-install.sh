#!/bin/bash

REPO_PATH=/home/aiida/aiida-core

git clone https://github.com/aiidateam/aiida-core.git --origin upstream $REPO_PATH

pip install --user -e "$REPO_PATH/[pre-commit,atomic_tools,docs,rest,tests,tui]" tox
