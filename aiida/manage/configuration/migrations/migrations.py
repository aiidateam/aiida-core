# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Define the current configuration version and migrations."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__all__ = ('CURRENT_CONFIG_VERSION', 'OLDEST_COMPATIBLE_CONFIG_VERSION')

# The expected version of the configuration file and the oldest backwards compatible configuration version.
# If the configuration file format is changed, the current version number should be upped and a migration added.
# When the configuration file format is changed in a backwards-incompatible way, the oldest compatible version should
# be set to the new current version.
CURRENT_CONFIG_VERSION = 3
OLDEST_COMPATIBLE_CONFIG_VERSION = 3


class ConfigMigration(object):  # pylint: disable=useless-object-inheritance
    """Defines a config migration."""

    def __init__(self, migrate_function, version, version_oldest_compatible):
        """Construct a ConfigMigration

        :param migrate_function: function which migrates the configuration dictionary
        :param version: configuration version after the migration.
        :param version_oldest_compatible: oldest compatible configuration version after the migration.
        """
        self.migrate_function = migrate_function
        self.version = int(version)
        self.version_oldest_compatible = int(version_oldest_compatible)

    def apply(self, config):
        """Apply the migration to the configuration."""
        config = self.migrate_function(config)
        config.version = self.version
        config.version_oldest_compatible = self.version_oldest_compatible
        return config


def _1_add_profile_uuid(config):
    """
    This adds the required values for a new default profile

        * PROFILE_UUID

    The profile uuid will be used as a general purpose identifier for the profile, in
    for example the RabbitMQ message queues and exchanges.
    """
    for profile in config.profiles:
        profile.uuid = profile.generate_uuid()
        config.update_profile(profile)

    return config


def _2_simplify_default_profiles(config):
    """
    The concept of a different 'process' for a profile has been removed and as such the
    default profiles key in the configuration no longer needs a value per process ('verdi', 'daemon')
    We remove the dictionary 'default_profiles' and replace it with a simple value 'default_profile'
    """
    from aiida.backends import settings

    default_profiles = config.dictionary.pop('default_profiles', None)

    if default_profiles:
        default_profile = default_profiles['daemon']
    else:
        default_profile = settings.AIIDADB_PROFILE

    config.set_default_profile(default_profile)

    return config


# Maps the initial config version to the ConfigMigration which updates it.
_MIGRATION_LOOKUP = {
    0: ConfigMigration(migrate_function=lambda x: x, version=1, version_oldest_compatible=0),
    1: ConfigMigration(migrate_function=_1_add_profile_uuid, version=2, version_oldest_compatible=0),
    2: ConfigMigration(migrate_function=_2_simplify_default_profiles, version=3, version_oldest_compatible=3)
}
