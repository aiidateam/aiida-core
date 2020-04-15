# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=wrong-import-order
"""Setup script for aiida-core package."""
import json
import sys
import os

from utils import fastentrypoints  # pylint: disable=unused-import
from setuptools import setup, find_packages

if (sys.version_info.major, sys.version_info.minor) == (3, 5):
    import setuptools
    from distutils.version import StrictVersion

    REQUIRED_SETUPTOOLS_VERSION = StrictVersion('38.2.0')
    INSTALLED_SETUPTOOLS_VERSION = StrictVersion(setuptools.__version__)

    if INSTALLED_SETUPTOOLS_VERSION < REQUIRED_SETUPTOOLS_VERSION:
        raise RuntimeError(
            'The installation of AiiDA with Python version 3.5, requires setuptools>={}; your version: {}'.format(
                REQUIRED_SETUPTOOLS_VERSION, INSTALLED_SETUPTOOLS_VERSION
            )
        )

if __name__ == '__main__':
    THIS_FOLDER = os.path.split(os.path.abspath(__file__))[0]

    with open(os.path.join(THIS_FOLDER, 'setup.json'), 'r') as info:
        SETUP_JSON = json.load(info)

    SETUP_JSON['extras_require']['testing'] = set(
        SETUP_JSON['extras_require']['testing'] + SETUP_JSON['extras_require']['rest'] +
        SETUP_JSON['extras_require']['atomic_tools']
    )

    SETUP_JSON['extras_require']['docs'] = set(
        SETUP_JSON['extras_require']['docs'] + SETUP_JSON['extras_require']['rest'] +
        SETUP_JSON['extras_require']['atomic_tools']
    )

    SETUP_JSON['extras_require']['all'] = list({
        item for sublist in SETUP_JSON['extras_require'].values() for item in sublist if item != 'bpython'
    })

    setup(
        packages=find_packages(),
        long_description=open(os.path.join(THIS_FOLDER, 'README.md')).read(),
        long_description_content_type='text/markdown',
        **SETUP_JSON
    )
