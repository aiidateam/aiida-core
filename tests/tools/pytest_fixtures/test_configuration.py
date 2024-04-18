"""Test the pytest fixtures."""

import tempfile


def test_aiida_config():
    """Test that ``aiida_config`` fixture is loaded by default and creates a config instance in temp directory."""
    from aiida.manage.configuration import get_config
    from aiida.manage.configuration.config import Config

    config = get_config()
    assert isinstance(config, Config)
    assert config.dirpath.startswith(tempfile.gettempdir())


def test_aiida_config_tmp(aiida_config_tmp):
    """Test that ``aiida_config_tmp`` returns a config instance in temp directory."""
    from aiida.manage.configuration.config import Config

    assert isinstance(aiida_config_tmp, Config)
    assert aiida_config_tmp.dirpath.startswith(tempfile.gettempdir())


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
