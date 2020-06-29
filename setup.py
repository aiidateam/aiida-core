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
import os
import sys

try:
    import fastentrypoints  # pylint: disable=unused-import
except ImportError:
    # This should only occur when building the package, i.e. when
    # executing 'python setup.py sdist' or 'python setup.py bdist_wheel'
    pass
from setuptools import setup, find_packages

if (sys.version_info.major, sys.version_info.minor) == (3, 5):
    import setuptools
    from distutils.version import StrictVersion

    REQUIRED_SETUPTOOLS_VERSION = StrictVersion('42.0.0')
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

    EXTRAS_REQUIRE = SETUP_JSON['extras_require']

    EXTRAS_REQUIRE['tests'] = set(EXTRAS_REQUIRE['tests'] + EXTRAS_REQUIRE['rest'] + EXTRAS_REQUIRE['atomic_tools'])

    EXTRAS_REQUIRE['docs'] = set(EXTRAS_REQUIRE['docs'] + EXTRAS_REQUIRE['rest'] + EXTRAS_REQUIRE['atomic_tools'])

    EXTRAS_REQUIRE['all'] = list({item for sublist in EXTRAS_REQUIRE.values() for item in sublist if item != 'bpython'})

    setup(
        packages=find_packages(include=['aiida', 'aiida.*']),
        long_description=open(os.path.join(THIS_FOLDER, 'README.md')).read(),
        long_description_content_type='text/markdown',
        **SETUP_JSON
    )
