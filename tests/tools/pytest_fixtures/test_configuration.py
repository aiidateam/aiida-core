"""Test the pytest fixtures."""

from pathlib import Path

from aiida.manage.configuration import get_config, load_config
from aiida.manage.configuration.settings import DEFAULT_CONFIG_FILE_NAME

# This is needed when we run this file in isolation using
# the `--noconftest` pytest option in the 'test-pytest-fixtures' CI job.
pytest_plugins = ['aiida.tools.pytest_fixtures']


def test_aiida_config(tmp_path_factory):
    """Test that ``aiida_config`` fixture is loaded by default and creates a config instance in temp directory."""
    from aiida.manage.configuration import CONFIG

    config = get_config(create=False)
    assert config is CONFIG
    assert config.dirpath.startswith(str(tmp_path_factory.getbasetemp()))
    assert Path(config.dirpath, DEFAULT_CONFIG_FILE_NAME).is_file()
    assert config._default_profile


def test_aiida_config_file(tmp_path_factory):
    """Test that ``aiida_config`` fixture stores the configuration in a config file in a temp directory."""
    # Unlike get_config, load_config always loads the configuration from a file
    config = load_config(create=False)
    assert config.dirpath.startswith(str(tmp_path_factory.getbasetemp()))
    assert Path(config.dirpath, DEFAULT_CONFIG_FILE_NAME).is_file()
    assert config._default_profile


def test_aiida_config_tmp(aiida_config_tmp, tmp_path_factory):
    """Test that ``aiida_config_tmp`` returns a config instance in temp directory."""
    from aiida.manage.configuration.config import Config

    assert isinstance(aiida_config_tmp, Config)
    assert aiida_config_tmp.dirpath.startswith(str(tmp_path_factory.getbasetemp()))


def test_aiida_profile():
    """Test that ``aiida_profile`` fixture is loaded by default and loads a temporary test profile."""
    from aiida.manage.configuration import get_profile
    from aiida.manage.configuration.profile import Profile

    profile = get_profile()
    assert isinstance(profile, Profile)
    assert profile.is_test_profile


def test_aiida_profile_tmp(aiida_profile, aiida_profile_tmp):
    """Test that ``aiida_profile_tmp`` returns a new profile instance in temporary config directory."""
    from aiida.manage.configuration.profile import Profile

    assert isinstance(aiida_profile_tmp, Profile)
    assert aiida_profile_tmp.is_test_profile
    assert aiida_profile_tmp.uuid != aiida_profile.uuid
