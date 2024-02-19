#!/bin/bash

cd ~ || exit
git clone https://github.com/aiidateam/aiida-core.git
cd aiida-core || exit
git remote rename origin upstream
pip install --user -e ."[pre-commit,atomic_tools,docs,rest,tests,tui]"
pip install tox
cd || exit
