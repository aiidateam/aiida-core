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

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_user
from aiida import orm

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


class TestVerdiUserCommand(AiidaTestCase):
    """Test verdi user."""

    def setUp(self):
        super().setUp()

        created, user = orm.User.objects.get_or_create(email=USER_1['email'])
        for key, _ in USER_1.items():
            if key != 'email':
                setattr(user, key, USER_1[key])
        if created:
            orm.User(**USER_1).store()
        self.cli_runner = CliRunner()

    def test_user_list(self):
        """Test `verdi user list`."""
        from aiida.cmdline.commands.cmd_user import user_list as list_user

        result = self.cli_runner.invoke(list_user, [], catch_exceptions=False)
        self.assertTrue(USER_1['email'] in result.output)

    def test_user_create(self):
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
        ]

        result = self.cli_runner.invoke(cmd_user.user_configure, cli_options, catch_exceptions=False)
        self.assertTrue(USER_2['email'] in result.output)
        self.assertTrue('created' in result.output)
        self.assertTrue('updated' not in result.output)

        user_obj = orm.User.objects.get(email=USER_2['email'])
        for key, val in USER_2.items():
            self.assertEqual(val, getattr(user_obj, key))

    def test_user_update(self):
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
        ]

        result = self.cli_runner.invoke(cmd_user.user_configure, cli_options, catch_exceptions=False)
        self.assertTrue(email in result.output)
        self.assertTrue('updated' in result.output)
        self.assertTrue('created' not in result.output)

        # Check it's all been changed to user2's attributes except the email
        for key, _ in USER_2.items():
            if key != 'email':
                setattr(cmd_user, key, USER_1[key])
