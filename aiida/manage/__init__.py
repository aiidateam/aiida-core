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
from .database import *
from .external import *
from .manager import *
from .tests import *

__all__ = (
    'BACKEND_UUID',
    'BROKER_DEFAULTS',
    'CONFIG',
    'CURRENT_CONFIG_VERSION',
    'CommunicationTimeout',
    'Config',
    'ConfigValidationError',
    'DEFAULT_DBINFO',
    'DeliveryFailed',
    'OLDEST_COMPATIBLE_CONFIG_VERSION',
    'Option',
    'PROFILE',
    'PluginTestCase',
    'Postgres',
    'PostgresConnectionMode',
    'ProcessLauncher',
    'Profile',
    'RemoteException',
    'TABLES_UUID_DEDUPLICATION',
    'TestRunner',
    'check_and_migrate_config',
    'config_needs_migrating',
    'config_schema',
    'deduplicate_uuids',
    'disable_caching',
    'enable_caching',
    'get_config',
    'get_config_option',
    'get_config_path',
    'get_current_version',
    'get_duplicate_uuids',
    'get_manager',
    'get_option',
    'get_option_names',
    'get_use_cache',
    'load_profile',
    'parse_option',
    'reset_config',
    'reset_manager',
    'verify_uuid_uniqueness',
    'write_database_integrity_violation',
)
