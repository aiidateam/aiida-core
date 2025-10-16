###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi user`."""

import itertools
import secrets

import pytest

from aiida import orm
from aiida.cmdline.commands import cmd_user


@pytest.fixture
def create_user():
    """Create a dictionary with random attributes for a new user."""
    return {
        'email': f'{secrets.token_hex(2)}@localhost',
        'first_name': secrets.token_hex(2),
        'last_name': secrets.token_hex(2),
        'institution': secrets.token_hex(2),
    }


@pytest.mark.usefixtures('aiida_profile')
def test_user_list(run_cli_command):
    """Test `verdi user list`."""
    default_user = orm.User.collection.get_default()
    result = run_cli_command(cmd_user.user_list)
    assert default_user.email in result.output


@pytest.mark.usefixtures('aiida_profile')
def test_user_configure_create(run_cli_command, create_user):
    """Create a new user with `verdi user configure`."""
    new_user = create_user
    options = list(
        itertools.chain(*zip(['--email', '--first-name', '--last-name', '--institution'], list(new_user.values())))
    )
    options.append('--set-default')

    result = run_cli_command(cmd_user.user_configure, options)
    assert new_user['email'] in result.output
    assert 'created' in result.output
    assert 'updated' not in result.output

    user = orm.User.collection.get(email=new_user['email'])
    for key, val in new_user.items():
        assert val == getattr(user, key)


@pytest.mark.usefixtures('aiida_profile')
def test_user_configure_update(run_cli_command, create_user):
    """Reconfigure an existing user with `verdi user configure`."""
    new_user = create_user
    default_user = orm.User.collection.get_default()
    new_user['email'] = default_user.email
    options = list(
        itertools.chain(*zip(['--email', '--first-name', '--last-name', '--institution'], list(new_user.values())))
    )
    options.append('--set-default')

    result = run_cli_command(cmd_user.user_configure, options)
    assert default_user.email in result.output
    assert 'updated' in result.output
    assert 'created' not in result.output

    for key, val in new_user.items():
        if key == 'email':
            continue
        assert val == getattr(default_user, key)


@pytest.mark.usefixtures('aiida_profile')
def test_set_default(run_cli_command, create_user):
    """Reconfigure an existing user with `verdi user configure`."""
    new_user = orm.User(**create_user).store()
    assert orm.User.collection.get_default().email != new_user.email

    result = run_cli_command(cmd_user.user_set_default, [new_user.email])
    assert f'Set `{new_user.email}` as the default user' in result.output
    assert orm.User.collection.get_default().email == new_user.email
