#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import os
import itertools
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

def find_path(root, dir_name):
    path = Path(os.path.abspath(root))
    for p in itertools.chain([path], path.parents):
        directory = p / dir_name
        if directory.is_dir():
            return directory
    raise OSError('No directory found')
