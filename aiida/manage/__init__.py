# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Managing an AiiDA instance:

    * configuration file
    * profiles
    * databases
    * repositories
    * external components (such as Postgres, RabbitMQ)

.. note:: Modules in this sub package may require the database environment to be loaded

"""

# AUTO-GENERATED

# yapf: disable
# pylint: disable=wildcard-import

from .caching import *
from .configuration import *
from .external import *
from .manager import *

__all__ = (
    'BROKER_DEFAULTS',
    'CURRENT_CONFIG_VERSION',
    'Config',
    'ConfigValidationError',
    'DEFAULT_DBINFO',
    'MIGRATIONS',
    'ManagementApiConnectionError',
    'OLDEST_COMPATIBLE_CONFIG_VERSION',
    'Option',
    'Postgres',
    'PostgresConnectionMode',
    'ProcessLauncher',
    'Profile',
    'RabbitmqManagementClient',
    'check_and_migrate_config',
    'config_needs_migrating',
    'config_schema',
    'disable_caching',
    'downgrade_config',
    'enable_caching',
    'get_current_version',
    'get_launch_queue_name',
    'get_manager',
    'get_message_exchange_name',
    'get_option',
    'get_option_names',
    'get_rmq_url',
    'get_task_exchange_name',
    'get_use_cache',
    'parse_option',
    'upgrade_config',
)

# yapf: enable
