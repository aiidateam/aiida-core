# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi setup`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from click.testing import CliRunner

from aiida.backends import settings
from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils.configuration import with_temporary_config_instance
from aiida.cmdline.commands import cmd_setup
from aiida.manage.configuration import get_config


class TestVerdiSetup(AiidaTestCase):
    """Tests for `verdi setup`."""

    def setUp(self):
        """Create runner object to run tests."""
        self.cli_runner = CliRunner()

    @with_temporary_config_instance
    def test_non_interactive_override(self):
        """Tests that existing profile can be overridden in non-interactive mode with the `--force` option."""
        config = get_config()
        profile = config.current_profile

        option_string = '--backend={backend} --email={email} --repository={repo} --db-host={db_host} ' \
                        '--db-port={db_port} --db-name={db_name} --db-username={db_user} --db-password={db_pass} ' \
                        '--first-name={first} --last-name={last} --institution={institution}'

        profile_settings = {
            'email': profile.dictionary['default_user_email'],
            'backend': profile.dictionary['AIIDADB_BACKEND'],
            'db_host': profile.dictionary['AIIDADB_HOST'],
            'db_port': profile.dictionary['AIIDADB_PORT'],
            'db_name': profile.dictionary['AIIDADB_NAME'],
            'db_user': profile.dictionary['AIIDADB_USER'],
            'db_pass': profile.dictionary['AIIDADB_PASS'],
            'repo': '/tmp',
            'first': 'nim',
            'last': 'porte',
            'institution': 'quoi',
        }

        options = ['--non-interactive'] + option_string.format(**profile_settings).split()

        # Without profile name should raise exception
        result = self.cli_runner.invoke(cmd_setup.setup, options)
        self.assertIsNotNone(result.exception)
        self.assertIn('Missing argument', result.output)
        self.assertIn('PROFILE_NAME', result.output)

        # With existing profile name should raise exception
        options.append(profile.name)
        result = self.cli_runner.invoke(cmd_setup.setup, options)
        self.assertIsNotNone(result.exception, result.output)

        # Need to set the current profile to None again, otherwise it will complain that `verdi` is using `-p` flag
        settings.AIIDADB_PROFILE = None

        # Adding the `--force` option should allow it
        options.append('--force')
        result = self.cli_runner.invoke(cmd_setup.setup, options)
        self.assertIsNone(result.exception, result.output)
