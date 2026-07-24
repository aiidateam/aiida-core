###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Define the current configuration version and migrations."""

from collections.abc import Iterable
from typing import Any, Protocol

from aiida.common import exceptions
from aiida.common.docs import URL_CONFIG_SCHEMA_COMPATIBILITY
from aiida.common.log import AIIDA_LOGGER

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

ConfigType = dict[str, Any]

# The expected version of the configuration file and the oldest backwards compatible configuration version.
# If the configuration file format is changed, the current version number should be upped and a migration added.
# When the configuration file format is changed in a backwards-incompatible way, the oldest compatible version should
# be set to the new current version.

CURRENT_CONFIG_VERSION = 10
OLDEST_COMPATIBLE_CONFIG_VERSION = 10
# Highest configuration version for which this code can run downgrade migrations, even if it cannot load it.
MAXIMUM_DOWNGRADE_CONFIG_VERSION = 10

CONFIG_LOGGER = AIIDA_LOGGER.getChild('config')


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
        from aiida.manage.configuration import get_profile

        global_profile = get_profile()
        default_profiles = config.pop('default_profiles', None)

        if default_profiles and 'daemon' in default_profiles:
            config['default_profile'] = default_profiles['daemon']
        elif default_profiles and 'verdi' in default_profiles:
            config['default_profile'] = default_profiles['verdi']
        elif global_profile is not None:
            config['default_profile'] = global_profile.name

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
        from aiida.brokers.rabbitmq.defaults import BROKER_DEFAULTS

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
        ('task_retry_initial_interval', 'transport.task_retry_initial_interval'),
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


class AbstractStorageAndProcess(SingleMigration):
    """Move the storage config under a top-level "storage" key and rabbitmq config under "processing".

    This allows for different storage backends to have different configuration.
    """

    down_revision = 5
    down_compatible = 5
    up_revision = 6
    up_compatible = 6

    storage_conversions = (
        ('AIIDADB_ENGINE', 'database_engine'),
        ('AIIDADB_HOST', 'database_hostname'),
        ('AIIDADB_PORT', 'database_port'),
        ('AIIDADB_USER', 'database_username'),
        ('AIIDADB_PASS', 'database_password'),
        ('AIIDADB_NAME', 'database_name'),
        ('AIIDADB_REPOSITORY_URI', 'repository_uri'),
    )
    process_keys = (
        'broker_protocol',
        'broker_username',
        'broker_password',
        'broker_host',
        'broker_port',
        'broker_virtual_host',
        'broker_parameters',
    )

    def upgrade(self, config: ConfigType) -> None:
        for profile_name, profile in config.get('profiles', {}).items():
            profile.setdefault('storage', {})
            if 'AIIDADB_BACKEND' not in profile:
                CONFIG_LOGGER.warning(f'profile {profile_name!r} had no expected "AIIDADB_BACKEND" key')
            profile['storage']['backend'] = profile.pop('AIIDADB_BACKEND', None)
            profile['storage'].setdefault('config', {})
            for old, new in self.storage_conversions:
                if old in profile:
                    profile['storage']['config'][new] = profile.pop(old)
                else:
                    CONFIG_LOGGER.warning(f'profile {profile_name!r} had no expected {old!r} key')
            profile.setdefault('process_control', {})
            profile['process_control']['backend'] = 'rabbitmq'
            profile['process_control'].setdefault('config', {})
            for key in self.process_keys:
                if key in profile:
                    profile['process_control']['config'][key] = profile.pop(key)
                elif key not in ('broker_parameters', 'broker_virtual_host'):
                    CONFIG_LOGGER.warning(f'profile {profile_name!r} had no expected {old!r} key')

    def downgrade(self, config: ConfigType) -> None:
        for profile_name, profile in config.get('profiles', {}).items():
            profile['AIIDADB_BACKEND'] = profile.get('storage', {}).get('backend', None)
            if profile['AIIDADB_BACKEND'] is None:
                CONFIG_LOGGER.warning(f'profile {profile_name!r} had no expected "storage.backend" key')
            for old, new in self.storage_conversions:
                if new in profile.get('storage', {}).get('config', {}):
                    profile[old] = profile['storage']['config'].pop(new)
            profile.pop('storage', None)
            for key in self.process_keys:
                if key in profile.get('process_control', {}).get('config', {}):
                    profile[key] = profile['process_control']['config'].pop(key)
            profile.pop('process_control', None)


class MergeStorageBackendTypes(SingleMigration):
    """`django` and `sqlalchemy` are now merged into `psql_dos`.

    The legacy name is stored under the `_v6_backend` key, to allow for downgrades.
    """

    down_revision = 6
    down_compatible = 6
    up_revision = 7
    up_compatible = 7

    def upgrade(self, config: ConfigType) -> None:
        for profile_name, profile in config.get('profiles', {}).items():
            if 'storage' in profile:
                storage = profile['storage']
                if 'backend' in storage:
                    if storage['backend'] in ('django', 'sqlalchemy'):
                        profile['storage']['_v6_backend'] = storage['backend']
                        storage['backend'] = 'psql_dos'
                    else:
                        CONFIG_LOGGER.warning(
                            f'profile {profile_name!r} had unknown storage backend {storage["backend"]!r}'
                        )

    def downgrade(self, config: ConfigType) -> None:
        for profile_name, profile in config.get('profiles', {}).items():
            if '_v6_backend' in profile.get('storage', {}):
                profile.setdefault('storage', {})['backend'] = profile['storage'].pop('_v6_backend')
            else:
                CONFIG_LOGGER.warning(f'profile {profile_name!r} had no expected "storage._v6_backend" key')


class AddTestProfileKey(SingleMigration):
    """Add the ``test_profile`` key."""

    down_revision = 7
    down_compatible = 7
    up_revision = 8
    up_compatible = 8

    def upgrade(self, config: ConfigType) -> None:
        for profile_name, profile in config.get('profiles', {}).items():
            profile['test_profile'] = profile_name.startswith('test_')

    def downgrade(self, config: ConfigType) -> None:
        profiles = config.get('profiles', {})
        profile_names = list(profiles.keys())

        # Iterate over the fixed list of the profile names, since we are mutating the profiles dictionary.
        for profile_name in profile_names:
            profile = profiles.pop(profile_name)
            profile_name_new = None
            test_profile = profile.pop('test_profile', False)  # If absent, assume it is not a test profile

            if test_profile and not profile_name.startswith('test_'):
                profile_name_new = f'test_{profile_name}'
                CONFIG_LOGGER.warning(
                    f'profile `{profile_name}` is a test profile but does not start with the required `test_` prefix.'
                )

            if not test_profile and profile_name.startswith('test_'):
                profile_name_new = profile_name[5:]
                CONFIG_LOGGER.warning(
                    f'profile `{profile_name}` is not a test profile but starts with the `test_` prefix.'
                )

            if profile_name_new is not None:
                if profile_name_new in profile_names:
                    raise exceptions.ConfigurationError(
                        f'cannot change `{profile_name}` to `{profile_name_new}` because it already exists.'
                    )

                CONFIG_LOGGER.warning(f'changing profile name from `{profile_name}` to `{profile_name_new}`.')
                profile_name = profile_name_new  # noqa: PLW2901

            profile['test_profile'] = test_profile
            profiles[profile_name] = profile


class AddPrefixToStorageBackendTypes(SingleMigration):
    """The ``storage.backend`` key should be prefixed with ``core.``.

    At this point, it should only ever contain ``psql_dos`` which should therefore become ``core.psql_dos``. To cover
    for cases where people manually added a read only ``sqlite_zip`` profile, we also migrate that.
    """

    down_revision = 8
    down_compatible = 8
    up_revision = 9
    up_compatible = 9

    def upgrade(self, config: ConfigType) -> None:
        for profile_name, profile in config.get('profiles', {}).items():
            if 'storage' in profile:
                backend = profile['storage'].get('backend', None)
                if backend in ('psql_dos', 'sqlite_zip', 'sqlite_temp'):
                    profile['storage']['backend'] = 'core.' + backend
                else:
                    CONFIG_LOGGER.warning(f'profile {profile_name!r} had unknown storage backend {backend!r}')

    def downgrade(self, config: ConfigType) -> None:
        for profile_name, profile in config.get('profiles', {}).items():
            backend = profile.get('storage', {}).get('backend', None)
            if backend in ('core.psql_dos', 'core.sqlite_zip', 'core.sqlite_temp'):
                profile.setdefault('storage', {})['backend'] = backend[5:]
            else:
                CONFIG_LOGGER.warning(
                    f'profile {profile_name!r} has storage backend {backend!r} that will not be compatible '
                    'with the version of `aiida-core` that can be used with the new version of the configuration.'
                )


class RenameRmqAndLogging(SingleMigration):
    """Migrate the logging (and related) configuration options introduced in version 10.

    Deprecated options are renamed to their replacements: ``logging.db_loglevel`` becomes ``logging.database_handler``
    and ``rmq.task_timeout`` becomes ``broker.task_timeout``. Any explicitly set value is moved to the new option.
    """

    down_revision = 9
    down_compatible = 9
    up_revision = 10
    up_compatible = 10

    option_renames = (
        ('logging.db_loglevel', 'logging.database_handler'),
        ('rmq.task_timeout', 'broker.task_timeout'),
    )
    advanced_logger_options = (
        'logging.verdi_loglevel',
        'logging.disk_objectstore_loglevel',
        'logging.plumpy_loglevel',
        'logging.kiwipy_loglevel',
        'logging.paramiko_loglevel',
        'logging.alembic_loglevel',
        'logging.sqlalchemy_loglevel',
        'logging.circus_loglevel',
        'logging.aiopika_loglevel',
    )
    v10_only_options = (
        'logging.aiida_core_loglevel',
        'logging.terminal_handler',
    )

    @classmethod
    def _rename_options(cls, options: dict[str, Any], *, downgrade: bool = False) -> None:
        """Rename deprecated options between the version 9 and 10 names."""
        for option_v9, option_v10 in cls.option_renames:
            source, target = (option_v10, option_v9) if downgrade else (option_v9, option_v10)
            if (value := options.pop(source, None)) is not None:
                options.setdefault(target, value)

    @classmethod
    def _remove_v10_only_options(cls, options: dict[str, Any]) -> None:
        """Remove options that did not exist before version 10."""
        for option_name in cls.v10_only_options:
            options.pop(option_name, None)

    @classmethod
    def _resolve_inherited_logger_options(cls, options: dict[str, Any], fallback_level: str) -> None:
        """Resolve ``INHERIT`` for advanced logger options to the effective ``logging.aiida_loglevel``."""
        for option_name in cls.advanced_logger_options:
            if options.get(option_name) == 'INHERIT':
                options[option_name] = fallback_level

    def upgrade(self, config: ConfigType) -> None:
        global_options = config.get('options', {})
        self._rename_options(global_options)

        for profile in config.get('profiles', {}).values():
            self._rename_options(profile.get('options', {}))

    def downgrade(self, config: ConfigType) -> None:
        global_options = config.get('options', {})
        global_fallback = global_options.get('logging.aiida_loglevel', 'REPORT')
        self._resolve_inherited_logger_options(global_options, global_fallback)
        self._rename_options(global_options, downgrade=True)
        self._remove_v10_only_options(global_options)

        for profile in config.get('profiles', {}).values():
            options = profile.get('options', {})
            profile_fallback = options.get('logging.aiida_loglevel', global_fallback)
            self._resolve_inherited_logger_options(options, profile_fallback)
            self._rename_options(options, downgrade=True)
            self._remove_v10_only_options(options)


MIGRATIONS = (
    Initial,
    AddProfileUuid,
    SimplifyDefaultProfiles,
    AddMessageBroker,
    SimplifyOptions,
    AbstractStorageAndProcess,
    MergeStorageBackendTypes,
    AddTestProfileKey,
    AddPrefixToStorageBackendTypes,
    RenameRmqAndLogging,
)


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


def config_can_be_downgraded(
    config: ConfigType,
    target: int | None = None,
    migrations: Iterable[type[SingleMigration]] = MIGRATIONS,
) -> bool:
    """Return whether the configuration can be downgraded to the target version.

    This is intentionally distinct from :data:`CURRENT_CONFIG_VERSION`: an AiiDA version may not be able to load a
    configuration for normal operation, but may still know enough migrations to rewrite it for an older version.

    :param config: the configuration dictionary
    :param target: the version to downgrade to, defaulting to :data:`CURRENT_CONFIG_VERSION`
    :param migrations: the registered migrations to consider
    :return: ``True`` if a chain of migrations exists to downgrade the configuration to the target version
    """
    target = CURRENT_CONFIG_VERSION if target is None else target
    current = get_current_version(config)

    if current <= target or current > MAXIMUM_DOWNGRADE_CONFIG_VERSION:
        return False

    used = []
    while current > target:
        try:
            migrator = next(m for m in migrations if m.up_revision == current)
        except StopIteration:
            return False
        if migrator in used:
            return False
        used.append(migrator)
        current = migrator.down_revision

    return current == target


def upgrade_config(
    config: ConfigType, target: int = CURRENT_CONFIG_VERSION, migrations: Iterable[type[SingleMigration]] = MIGRATIONS
) -> ConfigType:
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


def downgrade_config(
    config: ConfigType, target: int, migrations: Iterable[type[SingleMigration]] = MIGRATIONS
) -> ConfigType:
    """Run the registered configuration migrations down to the target version.

    :param config: the configuration dictionary
    :return: the migrated configuration dictionary
    """
    current = get_current_version(config)
    if current > MAXIMUM_DOWNGRADE_CONFIG_VERSION:
        msg = (
            f'Cannot downgrade configuration version {current}: this AiiDA version can only downgrade configuration '
            f'versions up to {MAXIMUM_DOWNGRADE_CONFIG_VERSION}.'
        )
        raise exceptions.ConfigurationError(msg)

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


def check_and_migrate_config(config, filepath: str | None = None):
    """Checks if the config needs to be migrated, and performs the migration if needed.

    :param config: the configuration dictionary
    :param filepath: the path to the configuration file (optional, for error reporting)
    :return: the migrated configuration dictionary
    """
    if config_needs_migrating(config, filepath):
        config = upgrade_config(config)

    return config


def config_needs_migrating(config, filepath: str | None = None):
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
        can_downgrade = config_can_be_downgraded(config)
        if can_downgrade:
            msg = (
                f'The AiiDA configuration file {filepath} has version {current_version} which is not compatible with '
                f'the current aiida version supporting up to version {CURRENT_CONFIG_VERSION}. '
                f'Run `verdi config downgrade {CURRENT_CONFIG_VERSION}` to rewrite it for this version. See '
                f'{URL_CONFIG_SCHEMA_COMPATIBILITY} for the compatibility table.'
            )
        else:
            msg = (
                f'The AiiDA configuration file {filepath} has version {current_version} which is not compatible with '
                f'the current aiida version supporting up to version {CURRENT_CONFIG_VERSION}. '
                'Before switching to an older AiiDA version, use a newer AiiDA version that supports '
                f'configuration version {current_version} and run `verdi config downgrade {CURRENT_CONFIG_VERSION}` '
                'to rewrite it for this version. See '
                f'{URL_CONFIG_SCHEMA_COMPATIBILITY} for the compatibility table.'
            )
        error = exceptions.ConfigurationVersionError(msg)
        error._can_downgrade = can_downgrade
        raise error

    return CURRENT_CONFIG_VERSION > current_version
