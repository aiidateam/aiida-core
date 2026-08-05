###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the configuration migration functionality."""

import copy
import json
import pathlib
import uuid

import pytest

from aiida.common.exceptions import ConfigurationError, ConfigurationVersionError
from aiida.manage.configuration.migrations import check_and_migrate_config
from aiida.manage.configuration.migrations.migrations import (
    MAXIMUM_DOWNGRADE_CONFIG_VERSION,
    MIGRATIONS,
    Initial,
    config_can_be_downgraded,
    downgrade_config,
    upgrade_config,
)


class CircularMigration(Initial):
    up_revision = 5
    down_revision = 5


@pytest.fixture
def load_config_sample():
    """Load a configuration file from a fixture."""

    def _factory(filename):
        with (pathlib.Path(__file__).parent / 'test_samples' / filename).open() as handle:
            return json.load(handle)

    return _factory


def test_upgrade_path_fail(load_config_sample):
    """Test failure when no upgrade path is available."""
    config_initial = load_config_sample('reference/5.json')
    # target lower than initial
    with pytest.raises(ConfigurationError):
        upgrade_config(copy.deepcopy(config_initial), 1)
    # no migration available
    with pytest.raises(ConfigurationError):
        upgrade_config(copy.deepcopy(config_initial), 100)
    # circular dependency
    with pytest.raises(ConfigurationError):
        upgrade_config(config_initial, 6, migrations=[CircularMigration])


def test_downgrade_path_fail(load_config_sample):
    """Test failure when no downgrade path is available."""
    config_initial = load_config_sample('reference/5.json')
    # target higher than initial
    with pytest.raises(ConfigurationError):
        downgrade_config(copy.deepcopy(config_initial), 6)
    # no migration available
    with pytest.raises(ConfigurationError):
        downgrade_config(copy.deepcopy(config_initial), -1)
    # circular dependency
    with pytest.raises(ConfigurationError):
        downgrade_config(config_initial, 4, migrations=[CircularMigration])


def test_config_needs_migrating_incompatible_version(monkeypatch):
    """An incompatible configuration version should raise with downgrade guidance."""
    from aiida.manage.configuration.migrations import migrations

    # Lower the loadable version below the downgrade cap so a config at the cap is unloadable but downgradeable,
    # exercising the can_downgrade guidance path (config_needs_migrating downgrades to CURRENT_CONFIG_VERSION).
    monkeypatch.setattr(migrations, 'CURRENT_CONFIG_VERSION', MAXIMUM_DOWNGRADE_CONFIG_VERSION - 1)
    config = {
        'CONFIG_VERSION': {
            'CURRENT': MAXIMUM_DOWNGRADE_CONFIG_VERSION,
            'OLDEST_COMPATIBLE': MAXIMUM_DOWNGRADE_CONFIG_VERSION,
        }
    }

    with pytest.raises(ConfigurationVersionError, match=r'verdi config downgrade') as exception:
        check_and_migrate_config(config, filepath='/tmp/config.json')

    assert exception.value._can_downgrade


def test_config_can_be_downgraded():
    """Test detecting whether a configuration can be downgraded by this AiiDA version.

    The migrations are passed as one-shot generators over a multi-step chain to ensure the iterable is materialized
    before being searched repeatedly (a consumed iterator would make the second lookup wrongly fail).
    """
    assert config_can_be_downgraded(
        {'CONFIG_VERSION': {'CURRENT': MAXIMUM_DOWNGRADE_CONFIG_VERSION, 'OLDEST_COMPATIBLE': 0}},
        target=MAXIMUM_DOWNGRADE_CONFIG_VERSION - 2,
        migrations=(m for m in MIGRATIONS),
    )
    assert not config_can_be_downgraded(
        {'CONFIG_VERSION': {'CURRENT': MAXIMUM_DOWNGRADE_CONFIG_VERSION + 1, 'OLDEST_COMPATIBLE': 0}},
        migrations=(m for m in MIGRATIONS),
    )


def test_migrate_full(load_config_sample, monkeypatch):
    """Test the full config migration."""
    config_initial = load_config_sample('input/0.json')
    # this should be always the most recent version
    config_target = load_config_sample('reference/10.json')

    # This change is necessary for the migration to version 2.
    monkeypatch.setattr(uuid, 'uuid4', lambda: uuid.UUID(hex='0' * 32))

    config_migrated = check_and_migrate_config(config_initial)
    assert config_migrated == config_target


def test_migrate_full_downgrade(load_config_sample, monkeypatch):
    """Test the full config downgrade, as a counterpart to :func:`test_migrate_full`.

    The oldest sample is upgraded to the latest version and then downgraded all the way back, exercising the full
    migration chain in both directions. Downgrades are lossy by design (e.g. a profile UUID added on upgrade is
    intentionally kept), so this asserts the versions reached rather than round-trip equality. The migrations are
    passed as one-shot generators, which additionally guards that the iterable is materialized before the repeated
    per-step lookups (a consumed iterator would stop finding migrations after the first step).
    """
    monkeypatch.setattr(uuid, 'uuid4', lambda: uuid.UUID(hex='0' * 32))

    upgraded = upgrade_config(load_config_sample('input/0.json'), 10, migrations=(m for m in MIGRATIONS))
    assert upgraded['CONFIG_VERSION']['CURRENT'] == 10

    downgraded = downgrade_config(upgraded, 0, migrations=(m for m in MIGRATIONS))
    assert downgraded['CONFIG_VERSION']['CURRENT'] == 0


@pytest.mark.parametrize('initial, target', ((m.down_revision, m.up_revision) for m in MIGRATIONS))
def test_migrate_individual(load_config_sample, initial, target, monkeypatch):
    """Test the individual config migrations."""
    config_initial = load_config_sample(f'input/{initial}.json')
    config_target = load_config_sample(f'reference/{target}.json')

    if target == 2:
        monkeypatch.setattr(uuid, 'uuid4', lambda: uuid.UUID(hex='0' * 32))

    config_migrated = upgrade_config(config_initial, target)
    assert config_migrated == config_target


def test_migrate_rmq_and_logging_leaves_unset_options_implicit():
    """Upgrade to version 10 should only rename explicit options and leave defaults implicit."""
    config = {
        'CONFIG_VERSION': {'CURRENT': 9, 'OLDEST_COMPATIBLE': 9},
        'profiles': {
            'default': {
                'storage': {'backend': 'core.psql_dos', 'config': {}},
                'process_control': {'backend': 'rabbitmq', 'config': {}},
            }
        },
    }

    migrated = upgrade_config(config, 10)

    assert 'options' not in migrated['profiles']['default']
    assert 'options' not in migrated


def test_migrate_rmq_and_logging_preserves_explicit_values():
    """Upgrade to version 10 should not overwrite explicitly configured logging options."""
    config = {
        'CONFIG_VERSION': {'CURRENT': 9, 'OLDEST_COMPATIBLE': 9},
        'profiles': {
            'default': {
                'storage': {'backend': 'core.psql_dos', 'config': {}},
                'process_control': {'backend': 'rabbitmq', 'config': {}},
                'options': {
                    'logging.verdi_loglevel': 'DEBUG',
                    'logging.db_loglevel': 'INFO',
                },
            }
        },
        'options': {
            'logging.plumpy_loglevel': 'ERROR',
            'rmq.task_timeout': 5,
        },
    }

    migrated = upgrade_config(config, 10)

    assert migrated['profiles']['default']['options'] == {
        'logging.verdi_loglevel': 'DEBUG',
        'logging.database_handler': 'INFO',
    }
    assert migrated['options'] == {
        'logging.plumpy_loglevel': 'ERROR',
        'broker.task_timeout': 5,
    }


def test_rename_rmq_and_logging_upgrade_renames_options():
    """Upgrade to version 10 should rename deprecated global and profile options."""
    config = {
        'CONFIG_VERSION': {'CURRENT': 9, 'OLDEST_COMPATIBLE': 9},
        'profiles': {
            'default': {
                'storage': {'backend': 'core.psql_dos', 'config': {}},
                'process_control': {'backend': 'rabbitmq', 'config': {}},
                'options': {
                    'logging.db_loglevel': 'INFO',
                    'rmq.task_timeout': 3,
                },
            }
        },
        'options': {
            'logging.db_loglevel': 'WARNING',
            'rmq.task_timeout': 5,
        },
    }

    migrated = upgrade_config(config, 10)

    assert migrated['options']['logging.database_handler'] == 'WARNING'
    assert migrated['options']['broker.task_timeout'] == 5
    assert 'logging.db_loglevel' not in migrated['options']
    assert 'rmq.task_timeout' not in migrated['options']

    profile_options = migrated['profiles']['default']['options']
    assert profile_options['logging.database_handler'] == 'INFO'
    assert profile_options['broker.task_timeout'] == 3
    assert 'logging.db_loglevel' not in profile_options
    assert 'rmq.task_timeout' not in profile_options


def test_rename_rmq_and_logging_downgrade_renames_options():
    """Downgrade to version 9 should rename replacement global and profile options back."""
    config = {
        'CONFIG_VERSION': {'CURRENT': 10, 'OLDEST_COMPATIBLE': 9},
        'profiles': {
            'default': {
                'storage': {'backend': 'core.psql_dos', 'config': {}},
                'process_control': {'backend': 'rabbitmq', 'config': {}},
                'options': {
                    'logging.database_handler': 'INFO',
                    'broker.task_timeout': 3,
                    'logging.aiida_core_loglevel': 'DEBUG',
                    'logging.terminal_handler': 'INFO',
                    'logging.disk_objectstore_loglevel': 'INHERIT',
                },
            }
        },
        'options': {
            'logging.database_handler': 'WARNING',
            'broker.task_timeout': 5,
            'logging.aiida_core_loglevel': 'DEBUG',
            'logging.terminal_handler': 'INFO',
            'logging.disk_objectstore_loglevel': 'INHERIT',
        },
    }

    migrated = downgrade_config(config, 9)

    assert migrated['options']['logging.db_loglevel'] == 'WARNING'
    assert migrated['options']['rmq.task_timeout'] == 5
    assert 'logging.database_handler' not in migrated['options']
    assert 'broker.task_timeout' not in migrated['options']
    assert 'logging.aiida_core_loglevel' not in migrated['options']
    assert 'logging.terminal_handler' not in migrated['options']

    profile_options = migrated['profiles']['default']['options']
    assert profile_options['logging.db_loglevel'] == 'INFO'
    assert profile_options['rmq.task_timeout'] == 3
    assert 'logging.database_handler' not in profile_options
    assert 'broker.task_timeout' not in profile_options
    assert 'logging.aiida_core_loglevel' not in profile_options
    assert 'logging.terminal_handler' not in profile_options


def test_rename_rmq_and_logging_downgrade_resolves_inherit_levels():
    """Downgrade to version 9 should resolve ``INHERIT`` to the effective ``logging.aiida_loglevel``."""
    config = {
        'CONFIG_VERSION': {'CURRENT': 10, 'OLDEST_COMPATIBLE': 9},
        'profiles': {
            'default': {
                'storage': {'backend': 'core.psql_dos', 'config': {}},
                'process_control': {'backend': 'rabbitmq', 'config': {}},
                'options': {
                    'logging.aiida_loglevel': 'INFO',
                    'logging.kiwipy_loglevel': 'INHERIT',
                    'logging.paramiko_loglevel': 'INHERIT',
                },
            },
            'other': {
                'storage': {'backend': 'core.psql_dos', 'config': {}},
                'process_control': {'backend': 'rabbitmq', 'config': {}},
                'options': {
                    'logging.circus_loglevel': 'INHERIT',
                },
            },
        },
        'options': {
            'logging.aiida_loglevel': 'ERROR',
            'logging.verdi_loglevel': 'INHERIT',
            'logging.plumpy_loglevel': 'INHERIT',
        },
    }

    migrated = downgrade_config(config, 9)

    assert migrated['options']['logging.verdi_loglevel'] == 'ERROR'
    assert migrated['options']['logging.plumpy_loglevel'] == 'ERROR'

    default_options = migrated['profiles']['default']['options']
    assert default_options['logging.kiwipy_loglevel'] == 'INFO'
    assert default_options['logging.paramiko_loglevel'] == 'INFO'

    other_options = migrated['profiles']['other']['options']
    assert other_options['logging.circus_loglevel'] == 'ERROR'


def test_merge_storage_backends_downgrade_profile(empty_config, profile_factory, caplog):
    """Test the downgrade of schema version 7.

    Test specifically the case that the ``storage._v6_backend`` key does not exist.
    """
    config = empty_config
    profile_a = profile_factory('profile_a', test_profile=False)
    profile_b = profile_factory('profile_b', test_profile=False)

    profile_a._attributes[profile_a.KEY_STORAGE]['_v6_backend'] = 'django'

    config.add_profile(profile_a)
    config.add_profile(profile_b)

    config_migrated = downgrade_config(config.dictionary, 6)
    assert list(config_migrated['profiles'].keys()) == ['profile_a', 'profile_b']
    assert f'profile {profile_b.name!r} had no expected "storage._v6_backend" key' in caplog.records[0].message


def test_add_test_profile_key_downgrade_profile(empty_config, profile_factory, caplog):
    """Test the downgrade of schema version 8.

    Test what happens if a configuration contains a normal profile whose name starts with ``test_``. In this case, it
    should automatically rename the profile by removing the prefix, unless that name already exists, in which case an
    exception should be raised.
    """
    config = empty_config
    profile = profile_factory('test_profile', test_profile=False)
    config.add_profile(profile)

    config_migrated = downgrade_config(config.dictionary, 7)
    assert list(config_migrated['profiles'].keys()) == ['profile']
    assert 'profile `test_profile` is not a test profile but starts with' in caplog.records[0].message
    assert 'changing profile name from `test_profile` to `profile`.' in caplog.records[1].message

    profile = profile_factory('profile')
    config.add_profile(profile)

    with pytest.raises(ConfigurationError, match=r'cannot change `.*` to `.*` because it already exists.'):
        downgrade_config(config.dictionary, 7)


def test_add_test_profile_key_downgrade_test_profile(empty_config, profile_factory, caplog):
    """Test the downgrade of schema version 8.

    Some special care needs to be taken in the downgrade in case the profile name does not have the correct heuristics
    with respect to its ``test_profile`` value, as the profile name is interpreted in schema version 7 and lower to
    determine whether a profile is a test profile or not.
    """
    config = empty_config
    profile = profile_factory('profile', test_profile=True)
    config.add_profile(profile)

    config_migrated = downgrade_config(config.dictionary, 7)
    assert list(config_migrated['profiles'].keys()) == ['test_profile']
    assert 'profile `profile` is a test profile but does not start with' in caplog.records[0].message
    assert 'changing profile name from `profile` to `test_profile`.' in caplog.records[1].message

    profile = profile_factory('test_profile', test_profile=True)
    config.add_profile(profile)

    with pytest.raises(ConfigurationError, match=r'cannot change `.*` to `.*` because it already exists.'):
        downgrade_config(config.dictionary, 7)
