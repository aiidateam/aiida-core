# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Modules related to the configuration of an AiiDA instance."""

# AUTO-GENERATED
# yapf: disable
# pylint: disable=wildcard-import

from .config import *
from .main import *
from .migrations import *
from .options import *
from .profile import *

__all__ = (
    'BACKEND_UUID',
    'CONFIG',
    'CURRENT_CONFIG_VERSION',
    'Config',
    'ConfigValidationError',
    'OLDEST_COMPATIBLE_CONFIG_VERSION',
    'Option',
    'PROFILE',
    'Profile',
    'check_and_migrate_config',
    'config_needs_migrating',
    'config_schema',
    'get_config',
    'get_config_option',
    'get_config_path',
    'get_current_version',
    'get_option',
    'get_option_names',
    'load_profile',
    'parse_option',
    'reset_config',
)
