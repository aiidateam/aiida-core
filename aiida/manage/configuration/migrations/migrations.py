# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Define the current configuration version and migrations."""

__all__ = ('CURRENT_CONFIG_VERSION', 'OLDEST_COMPATIBLE_CONFIG_VERSION')

# The expected version of the configuration file and the oldest backwards compatible configuration version.
# If the configuration file format is changed, the current version number should be upped and a migration added.
# When the configuration file format is changed in a backwards-incompatible way, the oldest compatible version should
# be set to the new current version.
CURRENT_CONFIG_VERSION = 4
OLDEST_COMPATIBLE_CONFIG_VERSION = 3


class ConfigMigration:
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
        config.setdefault('CONFIG_VERSION', {})['CURRENT'] = self.version
        config.setdefault('CONFIG_VERSION', {})['OLDEST_COMPATIBLE'] = self.version_oldest_compatible
        return config


def _1_add_profile_uuid(config):
    """Add the required values for a new default profile.

        * PROFILE_UUID

    The profile uuid will be used as a general purpose identifier for the profile, in
    for example the RabbitMQ message queues and exchanges.
    """
    for profile in config.get('profiles', {}).values():
        from uuid import uuid4
        profile['PROFILE_UUID'] = uuid4().hex

    return config


def _2_simplify_default_profiles(config):
    """Replace process specific default profiles with single default profile key.

    The concept of a different 'process' for a profile has been removed and as such the default profiles key in the
    configuration no longer needs a value per process ('verdi', 'daemon'). We remove the dictionary 'default_profiles'
    and replace it with a simple value 'default_profile'.
    """
    from aiida.manage.configuration import PROFILE

    default_profiles = config.pop('default_profiles', None)

    if default_profiles and 'daemon' in default_profiles:
        config['default_profile'] = default_profiles['daemon']
    elif default_profiles and 'verdi' in default_profiles:
        config['default_profile'] = default_profiles['verdi']
    elif PROFILE is not None:
        config['default_profile'] = PROFILE.name

    return config


def _3_add_message_broker(config):
    """Add the configuration for the message broker, which was not configurable up to now."""
    from aiida.manage.external.rmq import BROKER_DEFAULTS

    defaults = [
        ('broker_protocol', BROKER_DEFAULTS.protocol),
        ('broker_username', BROKER_DEFAULTS.username),
        ('broker_password', BROKER_DEFAULTS.password),
        ('broker_host', BROKER_DEFAULTS.host),
        ('broker_port', BROKER_DEFAULTS.port),
        ('broker_virtual_host', BROKER_DEFAULTS.virtual_host),
    ]

    for profile in config.get('profiles', {}).values():
        for key, default in defaults:
            if key not in profile:
                profile[key] = default

    return config


# Maps the initial config version to the ConfigMigration which updates it.
_MIGRATION_LOOKUP = {
    0: ConfigMigration(migrate_function=lambda x: x, version=1, version_oldest_compatible=0),
    1: ConfigMigration(migrate_function=_1_add_profile_uuid, version=2, version_oldest_compatible=0),
    2: ConfigMigration(migrate_function=_2_simplify_default_profiles, version=3, version_oldest_compatible=3),
    3: ConfigMigration(migrate_function=_3_add_message_broker, version=4, version_oldest_compatible=3)
}
