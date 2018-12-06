# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import print_function

from __future__ import absolute_import
import fastentrypoints
import re
import sys
import json
from distutils.version import StrictVersion
from os import path
from setuptools import setup, find_packages

if __name__ == '__main__':
    aiida_folder = path.split(path.abspath(__file__))[0]

    # Ensure that pip is installed and the version is at least 10.0.0, which is required for the build process
    try:
        import pip
    except ImportError:
        print('Could not import pip, which is required for installation')
        sys.exit(1)

    PIP_REQUIRED_VERSION = '10.0.0'
    required_version = StrictVersion(PIP_REQUIRED_VERSION)
    installed_version = StrictVersion(pip.__version__)

    if installed_version < required_version:
        print('The installation requires pip>={}, whereas currently {} is installed'.format(
            required_version, installed_version))
        sys.exit(1)

    with open(path.join(aiida_folder, 'setup.json'), 'r') as info:
        setup_json = json.load(info)

    setup_json['extras_require'][
        'testing'] += setup_json['extras_require']['rest'] + setup_json['extras_require']['atomic_tools'] + setup_json['extras_require']['docs']

    setup_json['extras_require']['all'] = list(
        {item for sublist in setup_json['extras_require'].values() for item in sublist if item != 'bpython'})

    setup(
        **setup_json,
        packages=find_packages(),
        long_description=open(path.join(aiida_folder, 'README.md')).read(),
        long_description_content_type='text/markdown',
    )
