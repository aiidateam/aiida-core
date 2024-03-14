#!/bin/bash

REPO_PATH=/home/aiida/aiida-core

# If the repo is not already existent, clone it
# This is only necessary if the image is run through k8s with persistent volume, as the volume will be empty
# For the docker, the container folder (i.e. `$HOME`) that mounted to the volume will be copied to the volume.
if [ ! -d "$REPO_PATH" ]; then
    git clone https://github.com/aiidateam/aiida-core.git --origin upstream $REPO_PATH
fi

pip install --user -e "$REPO_PATH/[pre-commit,atomic_tools,docs,rest,tests,tui]" tox
