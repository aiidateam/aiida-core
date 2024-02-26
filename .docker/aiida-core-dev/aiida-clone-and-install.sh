#!/bin/bash

cd ~ || exit
git clone https://github.com/aiidateam/aiida-core.git --origin upstream
cd aiida-core || exit
pip install --user -e ."[pre-commit,atomic_tools,docs,rest,tests,tui]"
pip install tox
cd || exit
