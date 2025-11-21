###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Managing an AiiDA instance:

    * configuration file
    * profiles
    * databases
    * repositories
    * external components (such as Postgres, RabbitMQ)

.. note:: Modules in this sub package may require the database environment to be loaded

"""

# AUTO-GENERATED
# fmt: off
from .caching import *
from .configuration import *
from .manager import *

__all__ = (
    'CURRENT_CONFIG_VERSION',
    'MIGRATIONS',
    'OLDEST_COMPATIBLE_CONFIG_VERSION',
    'AiiDAConfigDir',
    'AiiDAConfigPathResolver',
    'Option',
    'Profile',
    'check_and_migrate_config',
    'config_needs_migrating',
    'disable_caching',
    'downgrade_config',
    'enable_caching',
    'get_current_version',
    'get_manager',
    'get_option',
    'get_option_names',
    'get_use_cache',
    'parse_option',
    'upgrade_config',
)
# fmt: on
