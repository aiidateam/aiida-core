# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi`."""
from click.testing import CliRunner

from aiida import get_version
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_verdi

from tests.utils.configuration import with_temporary_config_instance


class TestVerdi(AiidaTestCase):
    """Tests for `verdi`."""

    def setUp(self):
        super().setUp()
        self.cli_runner = CliRunner()

    def test_verdi_version(self):
        """Regression test for #2238: verify that `verdi --version` prints the current version"""
        result = self.cli_runner.invoke(cmd_verdi.verdi, ['--version'])
        self.assertIsNone(result.exception, result.output)
        self.assertIn(get_version(), result.output)

    @with_temporary_config_instance
    def test_verdi_with_empty_profile_list(self):
        """Regression test for #2424: verify that verdi remains operable even if profile list is empty"""
        from aiida.manage.configuration import CONFIG

        # Run verdi command with updated CONFIG featuring an empty profile list
        CONFIG.dictionary[CONFIG.KEY_PROFILES] = {}
        result = self.cli_runner.invoke(cmd_verdi.verdi, [])
        self.assertIsNone(result.exception, result.output)

    @with_temporary_config_instance
    def test_invalid_cmd_matches(self):
        """Test that verdi with an invalid command will return matches if somewhat close"""
        result = self.cli_runner.invoke(cmd_verdi.verdi, ['usr'])
        self.assertIn('is not a verdi command', result.output)
        self.assertIn('The most similar commands are', result.output)
        self.assertIn('user', result.output)
        self.assertNotEqual(result.exit_code, 0)

    @with_temporary_config_instance
    def test_invalid_cmd_no_matches(self):
        """Test that verdi with an invalid command with no matches returns an appropriate message"""
        result = self.cli_runner.invoke(cmd_verdi.verdi, ['foobar'])
        self.assertIn('is not a verdi command', result.output)
        self.assertIn('No similar commands found', result.output)
        self.assertNotEqual(result.exit_code, 0)
