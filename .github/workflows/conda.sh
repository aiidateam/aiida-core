#!/usr/bin/env bash
set -ev

wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh;
bash miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
hash -r
conda config --set always_yes yes --set changeps1 no

# Workaround for https://github.com/conda/conda/issues/9337
pip uninstall -y setuptools
conda install setuptools

conda update -q conda
conda info -a
conda env create -f environment.yml -n test-environment python=$PYTHON_VERSION
