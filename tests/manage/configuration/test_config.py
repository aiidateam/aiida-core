###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the ``Config`` class."""

import json
import os
import pathlib
import uuid

import pytest

from aiida.common import exceptions
from aiida.manage.configuration import Profile, settings
from aiida.manage.configuration.config import Config
from aiida.manage.configuration.migrations import CURRENT_CONFIG_VERSION, OLDEST_COMPATIBLE_CONFIG_VERSION
from aiida.manage.configuration.options import get_option
from aiida.manage.configuration.settings import AiiDAConfigDir
from aiida.storage.sqlite_temp import SqliteTempBackend


class InvalidBaseStorage:
    pass


@pytest.fixture
def cache_aiida_path_variable():
    """Fixture that will store the ``AIIDA_PATH`` environment variable and restore it after the yield."""
    aiida_path_original = os.environ.get(settings.DEFAULT_AIIDA_PATH_VARIABLE)

    yield
    if aiida_path_original is not None:
        os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = aiida_path_original
    else:
        try:
            del os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE]
        except KeyError:
            pass

    # Make sure to reset the global variables set by the following call that are dependent on the environment variable
    # ``DEFAULT_AIIDA_PATH_VARIABLE``. It may have been changed by a test using this fixture.
    AiiDAConfigDir.set()


@pytest.mark.filterwarnings('ignore:Creating AiiDA configuration folder')
@pytest.mark.usefixtures('cache_aiida_path_variable')
def test_environment_variable_not_set(chdir_tmp_path, monkeypatch):
    """Check that if the environment variable is not set, config folder will be created in `DEFAULT_AIIDA_PATH`.

    To make sure we do not mess with the actual default `.aiida` folder, which often lives in the home folder
    we create a temporary directory and set the `DEFAULT_AIIDA_PATH` to it.

    Since if the environment variable is not set, the code will check for a config folder in the current working dir
    or any of its parents, we switch the working directory to the temporary path, which is unlikely to have a config
    directory in its hierarchy.
    """
    # Change the default configuration folder path to temp folder instead of probably `~`.
    monkeypatch.setattr(settings, 'DEFAULT_AIIDA_PATH', chdir_tmp_path)

    # Make sure that the environment variable is not set
    try:
        del os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE]
    except KeyError:
        pass
    AiiDAConfigDir.set()

    config_folder = chdir_tmp_path / settings.DEFAULT_CONFIG_DIR_NAME
    assert os.path.isdir(config_folder)
    assert AiiDAConfigDir.get() == pathlib.Path(config_folder)


@pytest.mark.filterwarnings('ignore:Creating AiiDA configuration folder')
@pytest.mark.usefixtures('cache_aiida_path_variable')
def test_environment_variable_set_single_path_without_config_folder(tmp_path):
    """If `AIIDA_PATH` is set but does not contain a configuration folder, it should be created."""
    # Set the environment variable and call configuration initialization
    os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = str(tmp_path)
    AiiDAConfigDir.set()

    # This should have created the configuration directory in the path
    config_folder = tmp_path / settings.DEFAULT_CONFIG_DIR_NAME
    assert config_folder.is_dir()
    assert AiiDAConfigDir.get() == config_folder


@pytest.mark.filterwarnings('ignore:Creating AiiDA configuration folder')
@pytest.mark.usefixtures('cache_aiida_path_variable')
def test_environment_variable_set_single_path_with_config_folder(tmp_path):
    """If `AIIDA_PATH` is set and already contains a configuration folder it should simply be used."""
    (tmp_path / settings.DEFAULT_CONFIG_DIR_NAME).mkdir()

    # Set the environment variable and call configuration initialization
    os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = str(tmp_path)
    AiiDAConfigDir.set()

    # This should have created the configuration directory in the path
    config_folder = tmp_path / settings.DEFAULT_CONFIG_DIR_NAME
    assert config_folder.is_dir()
    assert AiiDAConfigDir.get() == config_folder


@pytest.mark.filterwarnings('ignore:Creating AiiDA configuration folder')
@pytest.mark.usefixtures('cache_aiida_path_variable')
def test_environment_variable_path_including_config_folder(tmp_path):
    """If `AIIDA_PATH` is set and the path contains the base name of the config folder, it should work, i.e:

        `/home/user/.virtualenvs/dev/`
        `/home/user/.virtualenvs/dev/.aiida`

    Are both legal and will both result in the same configuration folder path.
    """
    # Set the environment variable with a path that include base folder name and call config initialization
    os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = str(tmp_path / settings.DEFAULT_CONFIG_DIR_NAME)
    AiiDAConfigDir.set()

    # This should have created the configuration directory in the pathpath
    config_folder = tmp_path / settings.DEFAULT_CONFIG_DIR_NAME
    assert config_folder.is_dir()
    assert AiiDAConfigDir.get() == config_folder


@pytest.mark.filterwarnings('ignore:Creating AiiDA configuration folder')
@pytest.mark.usefixtures('cache_aiida_path_variable')
def test_environment_variable_set_multiple_path(tmp_path):
    """If `AIIDA_PATH` is set with multiple paths without actual config folder, one is created in the last."""
    directory_a = tmp_path / 'a'
    directory_b = tmp_path / 'b'
    directory_c = tmp_path / 'c'

    directory_a.mkdir()
    directory_b.mkdir()
    directory_c.mkdir()

    # Set the environment variable to contain three paths and call configuration initialization
    env_variable = f'{directory_a}:{directory_b}:{directory_c}'
    os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = env_variable
    AiiDAConfigDir.set()

    # This should have created the configuration directory in the last path
    config_folder = directory_c / settings.DEFAULT_CONFIG_DIR_NAME
    assert os.path.isdir(config_folder)
    assert AiiDAConfigDir.get() == config_folder


def compare_config_in_memory_and_on_disk(config, filepath):
    """Verify that the contents of `config` are identical to the contents of the file with path `filepath`.

    :param config: instance of `Config`
    :param filepath: absolute filepath to a configuration file
    :raises AssertionError: if content of `config` is not equal to that of file on disk
    """
    in_memory = json.dumps(config.dictionary, indent=settings.DEFAULT_CONFIG_INDENT_SIZE)

    # Read the content stored on disk
    with open(filepath, 'r', encoding='utf8') as handle:
        on_disk = handle.read()

    # Compare content of in memory config and the one on disk
    assert in_memory == on_disk


def test_from_file(tmp_path):
    """Test the `Config.from_file` class method.

    Regression test for #3790: make sure configuration is written to disk after it is loaded and migrated.
    """
    # If the config file does not exist, a completely new file is created with a migrated config
    filepath_nonexisting = tmp_path / 'config_nonexisting.json'
    config = Config.from_file(filepath_nonexisting)

    # Make sure that the migrated config is written to disk, by loading it from disk and comparing to the content
    # of the in memory config object.
    compare_config_in_memory_and_on_disk(config, filepath_nonexisting)

    # Now repeat the test for an existing file. The previous filepath now *does* exist and is migrated
    filepath_existing = filepath_nonexisting
    config = Config.from_file(filepath_existing)

    compare_config_in_memory_and_on_disk(config, filepath_existing)

    # Finally, we test that an existing configuration file with an outdated schema is migrated and written to disk
    with (tmp_path / 'config.json').open('wb') as handle:
        # Write content of configuration with old schema to disk
        filepath = pathlib.Path(__file__).parent.absolute() / 'migrations' / 'test_samples' / 'input' / '0.json'
        with filepath.open('rb') as source:
            handle.write(source.read())
            handle.flush()

        config = Config.from_file(handle.name)
        compare_config_in_memory_and_on_disk(config, handle.name)


def test_from_file_no_migrate(config_with_profile):
    """Test that ``Config.from_file`` does not overwrite if the content was not migrated."""
    from time import sleep

    # Construct the ``Config`` instance and write it to disk
    config = config_with_profile
    config.store()

    timestamp = os.path.getmtime(config.filepath)
    Config.from_file(config.filepath)

    # Sleep a second, because for some operating systems the time resolution is of the order of a second
    sleep(1)

    assert os.path.getmtime(config.filepath) == timestamp


def test_basic_properties(config_with_profile):
    """Test the basic properties of the Config class."""
    config = config_with_profile

    assert isinstance(config.filepath, str)
    assert isinstance(config.dirpath, str)
    assert config.version == CURRENT_CONFIG_VERSION
    assert config.version_oldest_compatible == OLDEST_COMPATIBLE_CONFIG_VERSION
    assert isinstance(config.dictionary, dict)


def test_setting_versions(config_with_profile):
    """Test the version setters."""
    config = config_with_profile

    assert config.version == CURRENT_CONFIG_VERSION
    assert config.version_oldest_compatible == OLDEST_COMPATIBLE_CONFIG_VERSION

    new_config_version = 1000
    new_compatible_version = 999

    config.version = new_config_version
    config.version_oldest_compatible = new_compatible_version

    assert config.version == new_config_version
    assert config.version_oldest_compatible == new_compatible_version


def test_construct_empty_dictionary(tmp_path):
    """Constructing with empty dictionary should create basic skeleton."""
    config = Config(tmp_path, {})

    assert Config.KEY_PROFILES in config.dictionary
    assert Config.KEY_VERSION in config.dictionary
    assert Config.KEY_VERSION_CURRENT in config.dictionary[Config.KEY_VERSION]
    assert Config.KEY_VERSION_OLDEST_COMPATIBLE in config.dictionary[Config.KEY_VERSION]


def test_default_profile(empty_config, profile_factory):
    """Test setting and getting default profile."""
    config = empty_config

    # If not set should return None
    assert config.default_profile_name is None

    # Setting it to a profile that does not exist should raise
    with pytest.raises(exceptions.ProfileConfigurationError):
        config.set_default_profile('non_existing_profile')

    # After setting a default profile, it should return the right name
    profile = profile_factory()
    config.add_profile(profile)
    config.set_default_profile(profile.name)
    assert config.default_profile_name == profile.name

    # Setting it when a default is already set, should not overwrite by default
    alternative_profile_name = 'alternative_profile_name'
    alternative_profile = profile_factory(name=alternative_profile_name)
    config.add_profile(alternative_profile)
    config.set_default_profile(profile.name)
    assert config.default_profile_name == profile.name

    # But with overwrite=True it should
    config.set_default_profile(alternative_profile.name, overwrite=True)
    assert config.default_profile_name == alternative_profile_name


def test_set_default_user_email(config_with_profile):
    """Test the :meth:`aiida.manage.configuration.config.Config.set_default_user_email`."""
    config = config_with_profile
    profile = config.get_profile()
    default_user_email = profile.default_user_email
    default_user_email_new = uuid.uuid4().hex
    assert default_user_email != default_user_email_new
    config.set_default_user_email(profile, default_user_email_new)
    assert profile.default_user_email == default_user_email_new
    assert config.get_profile(profile.name).default_user_email == default_user_email_new


def test_profiles(config_with_profile, profile_factory):
    """Test the properties related to retrieving, creating, updating and removing profiles."""
    config = config_with_profile
    profile = config.get_profile()

    # Each item returned by config.profiles should be a Profile instance
    for profile in config.profiles:
        assert isinstance(profile, Profile)

    # The profile_names property should return the keys of the profiles dictionary
    assert config.profile_names == [profile.name]

    # Update a profile
    updated_profile = profile_factory(profile.name)
    config.update_profile(updated_profile)
    assert config.get_profile(updated_profile.name).dictionary == updated_profile.dictionary

    # Removing an unexisting profile should raise
    with pytest.raises(exceptions.ProfileConfigurationError):
        config.remove_profile('non_existing_profile')

    # Removing an existing should work and in this test case none should remain
    config.remove_profile(profile.name)
    assert config.profiles == []
    assert config.profile_names == []


def test_option(config_with_profile):
    """Test the setter, unsetter and getter of configuration options."""
    option_value = 131
    option_name = 'daemon.timeout'
    option = get_option(option_name)
    config = config_with_profile
    profile = config.get_profile()

    # Getting option that does not exist, should simply return the option default
    assert config.get_option(option_name, scope=profile.name) == option.default
    assert config.get_option(option_name, scope=None) == option.default

    # Unless we set default=False, in which case it should return None
    assert config.get_option(option_name, scope=profile.name, default=False) is None
    assert config.get_option(option_name, scope=None, default=False) is None

    # Setting an option profile configuration wide
    config.set_option(option_name, option_value)

    # Getting configuration wide should get new value but None for profile specific
    assert config.get_option(option_name, scope=None, default=False) == option_value
    assert config.get_option(option_name, scope=profile.name, default=False) is None

    # Setting an option profile specific
    config.set_option(option_name, option_value, scope=profile.name)
    assert config.get_option(option_name, scope=profile.name) == option_value

    # Unsetting profile specific
    config.unset_option(option_name, scope=profile.name)
    assert config.get_option(option_name, scope=profile.name, default=False) is None

    # Unsetting configuration wide
    config.unset_option(option_name, scope=None)
    assert config.get_option(option_name, scope=None, default=False) is None
    assert config.get_option(option_name, scope=None, default=True) == option.default

    # Setting a `None` like option
    option_value = 0
    config.set_option(option_name, option_value)
    assert config.get_option(option_name, scope=None, default=False) == option_value


def test_option_global_only(config_with_profile):
    """Test that `global_only` options are only set globally even if a profile specific scope is set."""
    option_name = 'autofill.user.email'
    option_value = 'some@email.com'

    config = config_with_profile
    profile = config.get_profile()

    # Setting an option globally should be fine
    config.set_option(option_name, option_value, scope=None)
    assert config.get_option(option_name, scope=None, default=False) == option_value

    # Setting an option profile specific should actually not set it on the profile since it is `global_only`
    config.set_option(option_name, option_value, scope=None)
    assert config.get_option(option_name, scope=profile.name, default=False) is None
    assert config.get_option(option_name, scope=None, default=False) == option_value


def test_set_option_override(config_with_profile):
    """Test that `global_only` options are only set globally even if a profile specific scope is set."""
    option_name = 'autofill.user.email'
    option_value_one = 'first@email.com'
    option_value_two = 'second@email.com'

    config = config_with_profile

    # Setting an option if it does not exist should work
    config.set_option(option_name, option_value_one)
    assert config.get_option(option_name, scope=None, default=False) == option_value_one

    # Setting it again will override it by default
    config.set_option(option_name, option_value_two)
    assert config.get_option(option_name, scope=None, default=False) == option_value_two

    # If we set override to False, it should not override, big surprise
    config.set_option(option_name, option_value_one, override=False)
    assert config.get_option(option_name, scope=None, default=False) == option_value_two


def test_option_empty_config(empty_config):
    """Test setting an option on a config without any profiles."""
    config = empty_config
    option_name = 'autofill.user.email'
    option_value = 'first@email.com'

    config.set_option(option_name, option_value)
    assert config.get_option(option_name, scope=None, default=False) == option_value


def test_store(config_with_profile):
    """Test that the store method writes the configuration properly to disk."""
    config = config_with_profile
    config.store()

    with open(config.filepath, 'r', encoding='utf8') as handle:
        config_recreated = Config(config.filepath, json.load(handle))

        assert config.dictionary == config_recreated.dictionary


def test_delete_profile(config_with_profile, profile_factory):
    """Test the ``delete_profile`` method."""
    config = config_with_profile
    profile_name = 'to-be-deleted'
    profile = profile_factory(name=profile_name)

    config.add_profile(profile)
    assert config.get_profile(profile_name) == profile

    # Write the contents to disk so that the to-be-deleted profile is in the config file on disk
    config.store()

    config.delete_profile(profile_name, delete_storage=False)
    assert profile_name not in config.profile_names

    # Now reload the config from disk to make sure the changes after deletion were persisted to disk
    config_on_disk = Config.from_file(config.filepath)
    assert profile_name not in config_on_disk.profile_names


@pytest.mark.parametrize(
    'file_exists,delete_storage,expected_messages',
    [
        # sqlite_zip with file exists - normal case
        (True, True, ['Data storage deleted']),
        # sqlite_zip with file exists, don't delete storage
        (True, False, ['Data storage not deleted']),
        # sqlite_zip with non-existent file
        (False, True, ["doesn't exist anymore", 'Possibly the file was manually removed']),
    ],
)
def test_delete_profile_sqlite_zip(
    config_with_profile, tmp_path, caplog, monkeypatch, file_exists, delete_storage, expected_messages
):
    """Test the ``delete_profile`` method with sqlite_zip backend in different scenarios."""
    import logging

    # Mock the validate_storage function to avoid needing a valid archive file
    from aiida.storage.sqlite_zip import migrator
    from aiida.storage.sqlite_zip.backend import SqliteZipBackend

    monkeypatch.setattr(migrator, 'validate_storage', lambda path: None)

    config = config_with_profile
    profile_name = 'sqlite-zip-test-profile'

    zip_filepath = tmp_path / f'{profile_name}.aiida'
    profile = SqliteZipBackend.create_profile(zip_filepath)
    profile._name = profile_name

    config.add_profile(profile)
    config.store()

    # Create file if it should exist and we have a valid path
    if file_exists:
        zip_filepath.write_bytes(b'dummy zip content')

    caplog.clear()

    with caplog.at_level(logging.INFO):
        config.delete_profile(profile_name, delete_storage=delete_storage)

    # Verify file handling
    if delete_storage and file_exists:
        assert not zip_filepath.exists()
    elif file_exists and not delete_storage:
        assert zip_filepath.exists()

    # Verify profile removal
    assert profile_name not in config.profile_names

    # Verify expected log messages
    all_messages = [record.message for record in caplog.records]
    for expected_message in expected_messages:
        assert any(expected_message in msg for msg in all_messages)


def test_create_profile_raises(config_with_profile, monkeypatch, entry_points):
    """Test the ``create_profile`` method when it raises."""
    config = config_with_profile
    profile_name = uuid.uuid4().hex

    def raise_storage_migration_error(*args, **kwargs):
        raise exceptions.StorageMigrationError()

    monkeypatch.setattr(SqliteTempBackend, 'initialise', raise_storage_migration_error)
    entry_points.add(InvalidBaseStorage, 'aiida.storage:core.invalid_base')

    with pytest.raises(ValueError, match=r'The profile `.*` already exists.'):
        config.create_profile(config_with_profile.default_profile_name, 'core.sqlite_temp', {})

    with pytest.raises(TypeError, match=r'The `storage_backend=.*` is not a subclass of `.*`.'):
        config.create_profile(profile_name, 'core.invalid_base', {})

    with pytest.raises(ValueError, match=r'The entry point `.*` could not be loaded'):
        config.create_profile(profile_name, 'core.non_existant', {})

    with pytest.raises(exceptions.StorageMigrationError, match='Storage backend initialisation failed.*'):
        config.create_profile(profile_name, 'core.sqlite_temp', {})


def test_create_profile(config_with_profile):
    """Test the ``create_profile`` method."""
    config = config_with_profile
    profile_name = uuid.uuid4().hex

    config.create_profile(profile_name, 'core.sqlite_temp', {})
    assert profile_name in config.profile_names
