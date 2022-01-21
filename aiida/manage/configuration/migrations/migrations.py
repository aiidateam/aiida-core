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
from typing import Any, Dict, Optional, Protocol

from aiida.common import exceptions

__all__ = (
    'CURRENT_CONFIG_VERSION', 'OLDEST_COMPATIBLE_CONFIG_VERSION', 'get_current_version', 'check_and_migrate_config',
    'config_needs_migrating', 'upgrade_config', 'downgrade_config'
)

ConfigType = Dict[str, Any]

# The expected version of the configuration file and the oldest backwards compatible configuration version.
# If the configuration file format is changed, the current version number should be upped and a migration added.
# When the configuration file format is changed in a backwards-incompatible way, the oldest compatible version should
# be set to the new current version.

CURRENT_CONFIG_VERSION = 5
OLDEST_COMPATIBLE_CONFIG_VERSION = 5


class SingleMigration(Protocol):
    """A single migration of the configuration."""

    down_revision: int
    """The initial configuration version."""

    down_compatible: int
    """The initial oldest backwards compatible configuration version"""

    up_revision: int
    """The final configuration version."""

    up_compatible: int
    """The final oldest backwards compatible configuration version"""

    def upgrade(self, config: ConfigType) -> None:
        """Migrate the configuration in-place."""

    def downgrade(self, config: ConfigType) -> None:
        """Downgrade the configuration in-place."""


class Initial(SingleMigration):
    """Base migration (no-op)."""
    down_revision = 0
    down_compatible = 0
    up_revision = 1
    up_compatible = 0

    def upgrade(self, config: ConfigType) -> None:
        pass

    def downgrade(self, config: ConfigType) -> None:
        pass


class AddProfileUuid(SingleMigration):
    """Add the required values for a new default profile.

        * PROFILE_UUID

    The profile uuid will be used as a general purpose identifier for the profile, in
    for example the RabbitMQ message queues and exchanges.
    """
    down_revision = 1
    down_compatible = 0
    up_revision = 2
    up_compatible = 0

    def upgrade(self, config: ConfigType) -> None:
        from uuid import uuid4  # we require this import here, to patch it in the tests
        for profile in config.get('profiles', {}).values():
            profile.setdefault('PROFILE_UUID', uuid4().hex)

    def downgrade(self, config: ConfigType) -> None:
        # leave the uuid present, so we could migrate back up
        pass


class SimplifyDefaultProfiles(SingleMigration):
    """Replace process specific default profiles with single default profile key.

    The concept of a different 'process' for a profile has been removed and as such the default profiles key in the
    configuration no longer needs a value per process ('verdi', 'daemon'). We remove the dictionary 'default_profiles'
    and replace it with a simple value 'default_profile'.
    """
    down_revision = 2
    down_compatible = 0
    up_revision = 3
    up_compatible = 3

    def upgrade(self, config: ConfigType) -> None:
        from aiida.manage.configuration import PROFILE

        default_profiles = config.pop('default_profiles', None)

        if default_profiles and 'daemon' in default_profiles:
            config['default_profile'] = default_profiles['daemon']
        elif default_profiles and 'verdi' in default_profiles:
            config['default_profile'] = default_profiles['verdi']
        elif PROFILE is not None:
            config['default_profile'] = PROFILE.name

    def downgrade(self, config: ConfigType) -> None:
        if 'default_profile' in config:
            default = config.pop('default_profile')
            config['default_profiles'] = {'daemon': default, 'verdi': default}


class AddMessageBroker(SingleMigration):
    """Add the configuration for the message broker, which was not configurable up to now."""
    down_revision = 3
    down_compatible = 3
    up_revision = 4
    up_compatible = 3

    def upgrade(self, config: ConfigType) -> None:
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

    def downgrade(self, config: ConfigType) -> None:
        pass


class SimplifyOptions(SingleMigration):
    """Remove unnecessary difference between file/internal representation of options"""
    down_revision = 4
    down_compatible = 3
    up_revision = 5
    up_compatible = 5

    conversions = (
        ('runner_poll_interval', 'runner.poll.interval'),
        ('daemon_default_workers', 'daemon.default_workers'),
        ('daemon_timeout', 'daemon.timeout'),
        ('daemon_worker_process_slots', 'daemon.worker_process_slots'),
        ('db_batch_size', 'db.batch_size'),
        ('verdi_shell_auto_import', 'verdi.shell.auto_import'),
        ('logging_aiida_log_level', 'logging.aiida_loglevel'),
        ('logging_db_log_level', 'logging.db_loglevel'),
        ('logging_plumpy_log_level', 'logging.plumpy_loglevel'),
        ('logging_kiwipy_log_level', 'logging.kiwipy_loglevel'),
        ('logging_paramiko_log_level', 'logging.paramiko_loglevel'),
        ('logging_alembic_log_level', 'logging.alembic_loglevel'),
        ('logging_sqlalchemy_loglevel', 'logging.sqlalchemy_loglevel'),
        ('logging_circus_log_level', 'logging.circus_loglevel'),
        ('user_email', 'autofill.user.email'),
        ('user_first_name', 'autofill.user.first_name'),
        ('user_last_name', 'autofill.user.last_name'),
        ('user_institution', 'autofill.user.institution'),
        ('show_deprecations', 'warnings.showdeprecations'),
        ('task_retry_down_revision_interval', 'transport.task_retry_initial_interval'),
        ('task_maximum_attempts', 'transport.task_maximum_attempts'),
    )

    def upgrade(self, config: ConfigType) -> None:
        for current, new in self.conversions:
            # replace in profile options
            for profile in config.get('profiles', {}).values():
                if current in profile.get('options', {}):
                    profile['options'][new] = profile['options'].pop(current)
            # replace in global options
            if current in config.get('options', {}):
                config['options'][new] = config['options'].pop(current)

    def downgrade(self, config: ConfigType) -> None:
        for current, new in self.conversions:
            # replace in profile options
            for profile in config.get('profiles', {}).values():
                if new in profile.get('options', {}):
                    profile['options'][current] = profile['options'].pop(new)
            # replace in global options
            if new in config.get('options', {}):
                config['options'][current] = config['options'].pop(new)


_MIGRATIONS = (Initial, AddProfileUuid, SimplifyDefaultProfiles, AddMessageBroker, SimplifyOptions)


def get_current_version(config):
    """Return the current version of the config.

    :return: current config version or 0 if not defined
    """
    return config.get('CONFIG_VERSION', {}).get('CURRENT', 0)


def get_oldest_compatible_version(config):
    """Return the current oldest compatible version of the config.

    :return: current oldest compatible config version or 0 if not defined
    """
    return config.get('CONFIG_VERSION', {}).get('OLDEST_COMPATIBLE', 0)


def upgrade_config(config: ConfigType, target: int = CURRENT_CONFIG_VERSION, migrations=_MIGRATIONS) -> ConfigType:
    """Run the registered configuration migrations up to the target version.

    :param config: the configuration dictionary
    :return: the migrated configuration dictionary
    """
    current = get_current_version(config)
    used = []
    while current < target:
        current = get_current_version(config)
        try:
            migrator = next(m for m in migrations if m.down_revision == current)
        except StopIteration:
            raise exceptions.ConfigurationError(f'No migration found to upgrade version {current}')
        if migrator in used:
            raise exceptions.ConfigurationError(f'Circular migration detected, upgrading to {target}')
        used.append(migrator)
        migrator().upgrade(config)
        current = migrator.up_revision
        config.setdefault('CONFIG_VERSION', {})['CURRENT'] = current
        config['CONFIG_VERSION']['OLDEST_COMPATIBLE'] = migrator.up_compatible
    if current != target:
        raise exceptions.ConfigurationError(f'Could not upgrade to version {target}, current version is {current}')
    return config


def downgrade_config(config: ConfigType, target: int, migrations=_MIGRATIONS) -> ConfigType:
    """Run the registered configuration migrations down to the target version.

    :param config: the configuration dictionary
    :return: the migrated configuration dictionary
    """
    current = get_current_version(config)
    used = []
    while current > target:
        current = get_current_version(config)
        try:
            migrator = next(m for m in migrations if m.up_revision == current)
        except StopIteration:
            raise exceptions.ConfigurationError(f'No migration found to downgrade version {current}')
        if migrator in used:
            raise exceptions.ConfigurationError(f'Circular migration detected, downgrading to {target}')
        used.append(migrator)
        migrator().downgrade(config)
        config.setdefault('CONFIG_VERSION', {})['CURRENT'] = current = migrator.down_revision
        config['CONFIG_VERSION']['OLDEST_COMPATIBLE'] = migrator.down_compatible
    if current != target:
        raise exceptions.ConfigurationError(f'Could not downgrade to version {target}, current version is {current}')
    return config


def check_and_migrate_config(config, filepath: Optional[str] = None):
    """Checks if the config needs to be migrated, and performs the migration if needed.

    :param config: the configuration dictionary
    :param filepath: the path to the configuration file (optional, for error reporting)
    :return: the migrated configuration dictionary
    """
    if config_needs_migrating(config, filepath):
        config = upgrade_config(config)

    return config


def config_needs_migrating(config, filepath: Optional[str] = None):
    """Checks if the config needs to be migrated.

    If the oldest compatible version of the configuration is higher than the current configuration version defined
    in the code, the config cannot be used and so the function will raise.

    :param filepath: the path to the configuration file (optional, for error reporting)
    :return: True if the configuration has an older version and needs to be migrated, False otherwise
    :raises aiida.common.ConfigurationVersionError: if the config's oldest compatible version is higher than the current
    """
    current_version = get_current_version(config)
    oldest_compatible_version = get_oldest_compatible_version(config)

    if oldest_compatible_version > CURRENT_CONFIG_VERSION:
        filepath = filepath if filepath else ''
        raise exceptions.ConfigurationVersionError(
            f'The configuration file has version {current_version} '
            f'which is not compatible with the current version {CURRENT_CONFIG_VERSION}: {filepath}\n'
            'Use a newer version of AiiDA to downgrade this configuration.'
        )

    return CURRENT_CONFIG_VERSION > current_version
