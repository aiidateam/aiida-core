"""Tests for :mod:`aiida.manage.configuration.settings`."""

import os

import pytest
from aiida.manage.configuration import settings


@pytest.fixture
def cache_aiida_path_variable():
    """Fixture that will store the ``AIIDA_PATH`` environment variable and restore it after the yield."""
    aiida_path_original = os.environ.pop(settings.DEFAULT_AIIDA_PATH_VARIABLE, None)

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
    settings.set_configuration_directory()


@pytest.mark.usefixtures('cache_aiida_path_variable', 'chdir_tmp_path')
def test_get_configuration_directory_default():
    """Test :meth:`aiida.manage.configuration.settings.get_configuration_directory`."""
    assert settings.get_configuration_directory() == settings.get_configuration_directory_default()


@pytest.mark.usefixtures('cache_aiida_path_variable')
def test_get_configuration_directory_cwd(chdir_tmp_path):
    """Test :meth:`aiida.manage.configuration.settings.get_configuration_directory`."""
    dirpath_config = chdir_tmp_path / settings.DEFAULT_CONFIG_DIR_NAME
    dirpath_config.mkdir()
    assert settings.get_configuration_directory() == dirpath_config


@pytest.mark.usefixtures('cache_aiida_path_variable')
def test_get_configuration_directory_cwd_parent(chdir_tmp_path):
    """Test :meth:`aiida.manage.configuration.settings.get_configuration_directory`."""
    dirpath_config = chdir_tmp_path / settings.DEFAULT_CONFIG_DIR_NAME
    dirpath_config.mkdir()
    dirpath_child = chdir_tmp_path / 'some' / 'sub' / 'directory'
    dirpath_child.mkdir(parents=True)
    os.chdir(dirpath_child)
    assert settings.get_configuration_directory() == dirpath_config


@pytest.mark.usefixtures('cache_aiida_path_variable')
def test_get_configuration_directory_path_variable(chdir_tmp_path):
    """Test :meth:`aiida.manage.configuration.settings.get_configuration_directory`."""
    dirpath_config = chdir_tmp_path / 'some_dir' / settings.DEFAULT_CONFIG_DIR_NAME
    dirpath_config.mkdir(parents=True)

    # Without the path variable specified, it should default to the default directory
    assert settings.get_configuration_directory() == settings.get_configuration_directory_default()

    # With the path variable set, that should now be the targeted directory
    os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = str(dirpath_config.absolute())
    assert settings.get_configuration_directory() == dirpath_config

    # If a config directory is now created in the cwd, it should ignore the path variable
    dirpath_config_cwd = chdir_tmp_path / settings.DEFAULT_CONFIG_DIR_NAME
    dirpath_config_cwd.mkdir()
    assert settings.get_configuration_directory() == dirpath_config_cwd
