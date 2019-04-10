# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi user`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_user
from aiida import orm

user_1 = {
    'email': "testuser1@localhost",
    'first_name': "Max",
    'last_name': "Mueller",
    'institution': "Testing Instiute"
}
user_2 = {
    'email': "testuser2@localhost",
    'first_name': "Sabine",
    'last_name': "Garching",
    'institution': "Second testing instiute"
}


class TestVerdiUserCommand(AiidaTestCase):

    def setUp(self):
        super(TestVerdiUserCommand, self).setUp()

        created, user = orm.User.objects.get_or_create(email=user_1['email'])
        for key, value in user_1.items():
            if key != 'email':
                setattr(user, key, user_1[key])
        if created:
            orm.User(**user_1).store()
        self.cli_runner = CliRunner()

    def test_user_list(self):
        """Test `verdi user list`."""
        from aiida.cmdline.commands.cmd_user import user_list as list_user

        result = self.cli_runner.invoke(list_user, [], catch_exceptions=False)
        self.assertTrue(user_1['email'] in result.output)

    def test_user_create(self):
        """Create a new user with `verdi user configure`."""
        cli_options = [
            '--email', user_2['email'],
            '--first-name', user_2['first_name'],
            '--last-name', user_2['last_name'],
            '--institution', user_2['institution'],
        ]

        result = self.cli_runner.invoke(cmd_user.user_configure, cli_options, catch_exceptions=False)
        self.assertTrue(user_2['email'] in result.output)
        self.assertTrue('created' in result.output)
        self.assertTrue('updated' not in result.output)

        user_obj = orm.User.objects.get(email=user_2['email'])
        for key, val in user_2.items():
            self.assertEqual(val, getattr(user_obj, key))

    def test_user_update(self):
        """Reconfigure an existing user with `verdi user configure`."""
        email = user_1['email']
        new_pass = '1234'

        cli_options = [
            '--email', user_1['email'],
            '--first-name', user_2['first_name'],
            '--last-name', user_2['last_name'],
            '--institution', user_2['institution'],
            '--password', new_pass,
        ]

        result = self.cli_runner.invoke(cmd_user.user_configure, cli_options, catch_exceptions=False)
        self.assertTrue(email in result.output)
        self.assertTrue('updated' in result.output)
        self.assertTrue('created' not in result.output)

        user_model = orm.User.objects.get(email=email)

        # Check it's all been changed to user2's attributes except the email
        for key, value in user_2.items():
            if key != 'email':
                setattr(cmd_user, key, user_1[key])

        self.assertTrue(user_model.verify_password(new_pass))
