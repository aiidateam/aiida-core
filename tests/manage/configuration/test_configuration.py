"""Tests for the :mod:`aiida.manage.configuration` module."""

import pytest

import aiida
from aiida.manage.configuration import Profile, create_profile, get_profile, profile_context
from aiida.manage.manager import get_manager


@pytest.mark.parametrize('entry_point', ('core.sqlite_temp', 'core.sqlite_dos'))
def test_create_profile(isolated_config, tmp_path, entry_point):
    """Test :func:`aiida.manage.configuration.tools.create_profile`."""
    profile_name = 'testing'
    profile = create_profile(
        isolated_config,
        name=profile_name,
        email='test@localhost',
        storage_backend=entry_point,
        storage_config={'filepath': str(tmp_path)},
    )
    assert isinstance(profile, Profile)
    assert profile_name in isolated_config.profile_names


def test_check_version_release(monkeypatch, capsys, isolated_config):
    """Test that ``Manager.check_version`` prints nothing for a release version.

    If a warning is emitted, it should be printed to stdout. So even though it will go through the logging system, the
    logging configuration of AiiDA will interfere with that of pytest and the ultimately the output will simply be
    written to stdout, so we use the ``capsys`` fixture and not the ``caplog`` one.
    """
    version = '1.0.0'
    monkeypatch.setattr(aiida, '__version__', version)

    # Explicitly setting the default in case the test profile has it changed.
    isolated_config.set_option('warnings.development_version', True)

    get_manager().check_version()
    captured = capsys.readouterr()
    assert not captured.err
    assert not captured.out


@pytest.mark.parametrize('suppress_warning', (True, False))
@pytest.mark.usefixtures('isolated_config')
def test_check_version_development(monkeypatch, suppress_warning):
    """Test that ``Manager.check_version`` prints a warning for a post release development version.

    The warning can be suppressed by setting the option ``warnings.development_version`` to ``False``.
    """
    from unittest.mock import MagicMock

    version = '1.0.0.post0'
    monkeypatch.setattr(aiida, '__version__', version)

    manager = get_manager()
    manager._profile.set_option('warnings.development_version', not suppress_warning)

    mock_warning = MagicMock()
    monkeypatch.setattr('aiida.cmdline.utils.echo.echo_warning', mock_warning)

    manager.check_version()

    if suppress_warning:
        mock_warning.assert_not_called()
    else:
        mock_warning.assert_called()
        first_call_msg = mock_warning.call_args_list[0][0][0]
        assert f'You are currently using a post release development version of AiiDA: {version}' in first_call_msg


def test_profile_context(config_with_profile, profile_factory):
    """Test that the original profile is restored when ``profile_context`` returns from the context."""
    config = config_with_profile

    # Get current profile
    profile_original = get_profile()
    assert profile_original is not None

    # Create a new profile and add it to the config
    profile_alternate = profile_factory()
    config.add_profile(profile_alternate)

    with profile_context(profile_alternate.name):
        assert get_profile() == profile_alternate

    assert get_profile() == profile_original
