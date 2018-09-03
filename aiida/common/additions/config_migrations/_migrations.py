# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

# The current configuration version. Increment this value whenever a change
# to the config.json structure is made.
from __future__ import absolute_import
CURRENT_CONFIG_VERSION = 3

# The oldest config version where no backwards-incompatible changes have been made since.
# When doing backwards-incompatible changes, set this to the current version.
OLDEST_COMPATIBLE_CONFIG_VERSION = 3


class ConfigMigration(object):
    """
    Defines a config migration.

    :param migrate_function: Function which transforms the config dict. This function does not need to change the CONFIG_VERSION values.

    :param current_version: Current config version after the migration.
    :type current_version: int

    :param oldest_version: Oldest compatible config version after the migration.
    :type oldest_version: int
    """
    def __init__(self, migrate_function, current_version, oldest_version):
        self.migrate_function = migrate_function
        self.current_version = int(current_version)
        self.oldest_version = int(oldest_version)

    def apply(self, config):
        from ._utils import VERSION_KEY, CURRENT_KEY, OLDEST_KEY
        from ._utils import add_config_version
        config = self.migrate_function(config)
        add_config_version(
            config,
            current_version=self.current_version,
            oldest_version=self.oldest_version
        )
        return config


def _1_add_profile_uuid(config):
    """
    This adds the required values for a new default profile

        * PROFILE_UUID

    The profile uuid will be used as a general purpose identifier for the profile, in
    for example the RabbitMQ message queues and exchanges.
    """
    from aiida.common.setup import generate_new_profile_uuid
    from aiida.common.setup import PROFILE_UUID_KEY

    profiles = config.get('profiles', {})

    for profile in profiles.values():
        profile[PROFILE_UUID_KEY] = generate_new_profile_uuid()

    return config


def _2_simplify_default_profiles(config):
    """
    The concept of a different 'process' for a profile has been removed and as such the
    default profiles key in the configuration no longer needs a value per process ('verdi', 'daemon')
    We remove the dictionary 'default_profiles' and replace it with a simple value 'default_profile'
    """
    from aiida.backends import settings

    default_profiles = config.pop('default_profiles', None)

    if default_profiles:
        default_profile = default_profiles['daemon']
    else:
        default_profile = settings.AIIDADB_PROFILE

    config['default_profile'] = default_profile

    return config


# Maps the initial config version to the ConfigMigration which updates it.
_MIGRATION_LOOKUP = {
    0: ConfigMigration(
        migrate_function=lambda x: x,
        current_version=1,
        oldest_version=0
    ),
    1: ConfigMigration(
        migrate_function=_1_add_profile_uuid,
        current_version=2,
        oldest_version=0
    ),
    2: ConfigMigration(
        migrate_function=_2_simplify_default_profiles,
        current_version=3,
        oldest_version=3
    )
}
