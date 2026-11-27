###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for development-version confirmation before changing storage."""

from types import SimpleNamespace

import pytest

from aiida.cmdline.commands import cmd_presto, cmd_profile, cmd_storage
from aiida.manage.configuration import get_profile, load_profile


@pytest.mark.parametrize('operation', ['presto', 'profile-setup', 'storage-migrate'])
def test_confirm_development_version(operation, run_cli_command, unacknowledged_config, monkeypatch, tmp_path):
    """Require an explicit yes even with --non-interactive or --force."""
    monkeypatch.setattr('aiida.__version__', '3.0.0.dev0')
    profile_name = 'development-test'

    if operation == 'presto':
        command = cmd_presto.verdi_presto
        parameters = ['--non-interactive', '--no-broker', '--profile-name', profile_name]
    elif operation == 'profile-setup':
        command = cmd_profile.profile_setup
        parameters = [
            'core.sqlite_dos',
            '--non-interactive',
            '--broker',
            'none',
            '--profile-name',
            profile_name,
            '--email',
            'email@host',
            '--filepath',
            tmp_path / 'storage',
        ]
    else:
        command = cmd_storage.storage_migrate
        parameters = ['--force']
        monkeypatch.setattr(
            'aiida.engine.daemon.client.get_daemon_client', lambda: SimpleNamespace(is_daemon_running=False)
        )

    prompt = 'Continue with this development version? [y/N]'
    success = 'migration completed' if operation == 'storage-migrate' else f'Created new profile `{profile_name}`.'
    for response in (None, '\n'):
        result = run_cli_command(command, parameters, user_input=response, raises=True)
        assert prompt in result.stderr
        assert success not in result.output
        assert profile_name not in unacknowledged_config.profile_names

    original_profile = get_profile()
    assert original_profile is not None
    try:
        result = run_cli_command(command, parameters, user_input='y\n')
        assert prompt in result.stderr
        assert success in result.output
    finally:
        load_profile(original_profile.name, allow_switch=True)
