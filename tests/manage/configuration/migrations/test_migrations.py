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

from aiida.common.exceptions import ConfigurationError
from aiida.manage.configuration.migrations import check_and_migrate_config
from aiida.manage.configuration.migrations.migrations import MIGRATIONS, Initial, downgrade_config, upgrade_config


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


def test_migrate_full(load_config_sample, monkeypatch):
    """Test the full config migration."""
    config_initial = load_config_sample('input/0.json')
    config_target = load_config_sample('reference/final.json')

    # This change is necessary for the migration to version 2.
    monkeypatch.setattr(uuid, 'uuid4', lambda: uuid.UUID(hex='0' * 32))

    config_migrated = check_and_migrate_config(config_initial)
    assert config_migrated == config_target


@pytest.mark.parametrize('initial, target', ((m.down_revision, m.up_revision) for m in MIGRATIONS))
def test_migrate_individual(load_config_sample, initial, target, monkeypatch):
    """Test the individual config migrations."""
    config_initial = load_config_sample(f'input/{initial}.json')
    config_target = load_config_sample(f'reference/{target}.json')

    if target == 2:
        monkeypatch.setattr(uuid, 'uuid4', lambda: uuid.UUID(hex='0' * 32))

    config_migrated = upgrade_config(config_initial, target)
    assert config_migrated == config_target


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
