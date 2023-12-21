###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Methods and definitions of migrations for the configuration file of an AiiDA instance."""

# AUTO-GENERATED

# fmt: off

from .migrations import *

__all__ = (
    'CURRENT_CONFIG_VERSION',
    'MIGRATIONS',
    'OLDEST_COMPATIBLE_CONFIG_VERSION',
    'check_and_migrate_config',
    'config_needs_migrating',
    'downgrade_config',
    'get_current_version',
    'upgrade_config',
)

# fmt: on
