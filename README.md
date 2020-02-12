# <img src="docs/source/images/AiiDA_transparent_logo.png" alt="AiiDA" width="200"/>

AiiDA (www.aiida.net) is a workflow manager for computational science with a strong focus on provenance, performance and extensibility.

|    | |
|-----|----------------------------------------------------------------------------|
|Latest release| [![PyPI version](https://badge.fury.io/py/aiida-core.svg)](https://badge.fury.io/py/aiida-core) [![conda-forge](https://img.shields.io/conda/vn/conda-forge/aiida-core.svg?style=flat)](https://anaconda.org/conda-forge/aiida-core) [![PyPI pyversions](https://img.shields.io/pypi/pyversions/aiida-core.svg)](https://pypi.python.org/pypi/aiida-core/) |
|Getting help| [![Docs status](https://readthedocs.org/projects/aiida-core/badge)](http://aiida-core.readthedocs.io/) [![Google Group](https://img.shields.io/badge/-Google%20Group-lightgrey.svg)](https://groups.google.com/forum/#!forum/aiidausers)
|Build status| [![Build Status](https://travis-ci.org/aiidateam/aiida-core.svg?branch=develop)](https://travis-ci.org/aiidateam/aiida-core) [![Coverage Status](https://coveralls.io/repos/github/aiidateam/aiida-core/badge.svg?branch=develop)](https://coveralls.io/github/aiidateam/aiida-core?branch=develop) |
|Activity| [![PyPI-downloads](https://img.shields.io/pypi/dm/aiida-core.svg?style=flat)](https://pypistats.org/packages/aiida-core) [![Commit Activity](https://img.shields.io/github/commit-activity/m/aiidateam/aiida-core.svg)](https://github.com/aiidateam/aiida-core/pulse)
|Community| [![Affiliated with NumFOCUS](https://img.shields.io/badge/NumFOCUS-affiliated%20project-orange.svg?style=flat&colorA=E1523D&colorB=007D8A)](https://numfocus.org/sponsored-projects/affiliated-projects) [![Twitter](https://img.shields.io/twitter/follow/aiidateam.svg?style=social&label=Follow)](https://twitter.com/aiidateam)


## Features

 -   **Workflows:** Write complex, auto-documenting workflows in
     python, linked to arbitrary executables on local and remote
     computers. The event-based workflow engine supports tens of
     thousands of processes per hour with full checkpointing.
 -   **Data provenance:** Automatically track inputs, outputs & metadata
     of all calculations in a provenance graph for full
     reproducibility. Perform fast queries on graphs containing
     millions of nodes.
 -   **HPC interface:** Move your calculations to a different computer
     by changing one line of code. AiiDA is compatible with schedulers
     like [SLURM](https://slurm.schedmd.com), [PBS
     Pro](https://www.pbspro.org/),
     [torque](http://www.adaptivecomputing.com/products/torque/),
     [SGE](http://gridscheduler.sourceforge.net/) or
     [LSF](https://www.ibm.com/support/knowledgecenter/SSETD4/product_welcome_platform_lsf.html)
     out of the box.
 -   **Plugin interface:** Extend AiiDA with [plugins](https://aiidateam.github.io/aiida-registry/) for new simulation codes (input generation & parsing), data types, schedulers, transport modes and more.
 -   **Open Science:** Export subsets of your provenance graph and share them with peers or make them available online for everyone
     on the [Materials Cloud](https://www.materialscloud.org).
 -   **Open source:** AiiDA is released under the [MIT open source license](LICENSE.txt)

## Installation

Please see AiiDA's [documentation](https://aiida-core.readthedocs.io/en/latest/).

## How to contribute [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com) [![GitHub issues by-label](https://img.shields.io/github/issues/aiidateam/aiida-core/good%20first%20issue)](https://github.com/aiidateam/aiida-core/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)

The AiiDA team appreciates help from a wide range of different backgrounds.
Small improvements of the documentation or minor bug fixes are always welcome.

Please see the [Contributor wiki](https://github.com/aiidateam/aiida-core/wiki) on how to get started.

## How to cite

If you use AiiDA in your research, please consider citing the AiiDA paper:

> Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari,
> and Boris Kozinsky, *AiiDA: automated interactive infrastructure and
> database for computational science*, Comp. Mat. Sci 111, 218-230
> (2016); <https://doi.org/10.1016/j.commatsci.2015.09.013>;
> <http://www.aiida.net>.

## License

AiiDA is distributed under the MIT open source license (see [`LICENSE.txt`](LICENSE.txt)).

For a list of other open source components included in AiiDA, see [`open_source_licenses.txt`](open_source_licenses.txt).

## Acknowledgements

This work is supported by:
* the [MARVEL National Centre for Competency in Research](http://nccr-marvel.ch) funded by the [Swiss National Science Foundation](http://www.snf.ch/en);
* the [MaX European Centre of Excellence](http://www.max-centre.eu/) funded by the Horizon 2020 EINFRA-5 program, Grant No. 676598;
* the [swissuniversities P-5 project "Materials Cloud"](https://www.materialscloud.org/swissuniversities).

<img src="docs/source/images/MARVEL.png" alt="MARVEL" style="padding:10px;" width="150"/>
<img src="docs/source/images/MaX.png" alt="MaX" style="padding:10px;" width="250"/>
<img src="docs/source/images/swissuniversities.png" alt="swissuniversities" style="padding:10px;" width="250"/>
