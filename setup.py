# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Setup script for aiida-core package."""

from __future__ import division
from __future__ import print_function

from __future__ import absolute_import
import sys
import json
from os import path
# pylint: disable=wrong-import-order
# Note: This speeds up command line scripts (e.g. verdi)
from utils import fastentrypoints  # pylint: disable=unused-import
from distutils.version import StrictVersion
from setuptools import setup, find_packages

if __name__ == '__main__':
    THIS_FOLDER = path.split(path.abspath(__file__))[0]

    # Ensure that pip is installed and the version is at least 10.0.0, which is required for the build process
    try:
        import pip
    except ImportError:
        print('Could not import pip, which is required for installation')
        sys.exit(1)

    PIP_REQUIRED_VERSION = '10.0.0'
    REQUIRED_VERSION = StrictVersion(PIP_REQUIRED_VERSION)
    INSTALLED_VERSION = StrictVersion(pip.__version__)

    if INSTALLED_VERSION < REQUIRED_VERSION:
        print('The installation requires pip>={}, whereas currently {} is installed'.format(
            REQUIRED_VERSION, INSTALLED_VERSION))
        sys.exit(1)

    with open(path.join(THIS_FOLDER, 'setup.json'), 'r') as info:
        SETUP_JSON = json.load(info)

    SETUP_JSON['extras_require']['testing'] \
        += SETUP_JSON['extras_require']['rest'] \
        + SETUP_JSON['extras_require']['atomic_tools']

    SETUP_JSON['extras_require']['docs'] \
        += SETUP_JSON['extras_require']['rest'] \
        + SETUP_JSON['extras_require']['atomic_tools']

    SETUP_JSON['extras_require']['all'] = list(
        {item for sublist in SETUP_JSON['extras_require'].values() for item in sublist if item != 'bpython'})

    setup(
        packages=find_packages(),
        long_description=open(path.join(THIS_FOLDER, 'README.md')).read(),
        long_description_content_type='text/markdown',
        **SETUP_JSON)
