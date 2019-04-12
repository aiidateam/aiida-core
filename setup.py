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
import json
from os import path
# pylint: disable=wrong-import-order
# Note: This speeds up command line scripts (e.g. verdi)
from utils import fastentrypoints  # pylint: disable=unused-import
from setuptools import setup, find_packages

if __name__ == '__main__':
    THIS_FOLDER = path.split(path.abspath(__file__))[0]

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
