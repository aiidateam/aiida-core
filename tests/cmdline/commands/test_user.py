# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi user`."""
import pytest

from aiida import orm
from aiida.cmdline.commands import cmd_user

USER_1 = {  # pylint: disable=invalid-name
    'email': 'testuser1@localhost',
    'first_name': 'Max',
    'last_name': 'Mueller',
    'institution': 'Testing Instiute'
}
USER_2 = {  # pylint: disable=invalid-name
    'email': 'testuser2@localhost',
    'first_name': 'Sabine',
    'last_name': 'Garching',
    'institution': 'Second testing instiute'
}


class TestVerdiUserCommand:
    """Test verdi user."""

    @pytest.fixture(autouse=True)
    def init_profile(self):  # pylint: disable=unused-argument
        """Initialize the profile."""
        # pylint: disable=attribute-defined-outside-init
        created, user = orm.User.collection.get_or_create(email=USER_1['email'])
        for key, value in USER_1.items():
            if key != 'email':
                setattr(user, key, value)
        if created:
            orm.User(**USER_1).store()

    def test_user_list(self, run_cli_command):
        """Test `verdi user list`."""
        from aiida.cmdline.commands.cmd_user import user_list as list_user

        result = run_cli_command(list_user, [])
        assert USER_1['email'] in result.output

    def test_user_create(self, run_cli_command):
        """Create a new user with `verdi user configure`."""
        cli_options = [
            '--email',
            USER_2['email'],
            '--first-name',
            USER_2['first_name'],
            '--last-name',
            USER_2['last_name'],
            '--institution',
            USER_2['institution'],
            '--set-default',
        ]

        result = run_cli_command(cmd_user.user_configure, cli_options)
        assert USER_2['email'] in result.output
        assert 'created' in result.output
        assert 'updated' not in result.output

        user_obj = orm.User.collection.get(email=USER_2['email'])
        for key, val in USER_2.items():
            assert val == getattr(user_obj, key)

    def test_user_update(self, run_cli_command):
        """Reconfigure an existing user with `verdi user configure`."""
        email = USER_1['email']

        cli_options = [
            '--email',
            USER_1['email'],
            '--first-name',
            USER_2['first_name'],
            '--last-name',
            USER_2['last_name'],
            '--institution',
            USER_2['institution'],
            '--set-default',
        ]

        result = run_cli_command(cmd_user.user_configure, cli_options)
        assert email in result.output
        assert 'updated' in result.output
        assert 'created' not in result.output

        # Check it's all been changed to user2's attributes except the email
        for key, _ in USER_2.items():
            if key != 'email':
                setattr(cmd_user, key, USER_1[key])
