#!/bin/bash
# See https://conda.io/docs/user-guide/tasks/use-conda-with-travis-ci.html#the-travis-yml-file
if [[ "$TRAVIS_PYTHON_VERSION" == "2.7" ]]; then
  wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh -O miniconda.sh;
else
  wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh;
fi
bash miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
hash -r
conda config --set always_yes yes --set changeps1 no

# workaround for https://github.com/conda/conda/issues/9337
pip uninstall -y setuptools
conda install setuptools

conda update -q conda
# Useful for debugging any issues with conda
conda info -a
