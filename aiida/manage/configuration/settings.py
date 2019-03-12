# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Base settings required for the configuration of an AiiDA instance."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

from aiida.common.folders import find_path

DEFAULT_UMASK = 0o0077
DEFAULT_AIIDA_PATH_VARIABLE = 'AIIDA_PATH'
DEFAULT_AIIDA_USER = 'aiida@localhost'
DEFAULT_CONFIG_DIR_BASE = '~'
DEFAULT_CONFIG_DIR_NAME = '.aiida'
DEFAULT_CONFIG_FILE_NAME = 'config.json'
DEFAULT_CONFIG_INDENT_SIZE = 4
DEFAULT_DAEMON_DIR_NAME = 'daemon'
DEFAULT_DAEMON_LOG_DIR_NAME = 'log'

AIIDA_PATH = [os.path.expanduser(path) for path in os.environ.get(DEFAULT_AIIDA_PATH_VARIABLE, '').split(':') if path]
AIIDA_PATH.append(os.path.expanduser('~'))

for path in AIIDA_PATH:
    try:
        AIIDA_CONFIG_FOLDER = os.path.expanduser(str(find_path(root=path, dir_name=DEFAULT_CONFIG_DIR_NAME)))
        break
    except OSError:
        pass
else:
    default_folder = os.path.join(DEFAULT_CONFIG_DIR_BASE, DEFAULT_CONFIG_DIR_NAME)
    AIIDA_CONFIG_FOLDER = os.path.expanduser(default_folder)

DAEMON_DIR = os.path.join(AIIDA_CONFIG_FOLDER, DEFAULT_DAEMON_DIR_NAME)
DAEMON_LOG_DIR = os.path.join(DAEMON_DIR, DEFAULT_DAEMON_LOG_DIR_NAME)
