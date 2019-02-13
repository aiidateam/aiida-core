# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from click.testing import CliRunner

from aiida import get_version
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_verdi


class TestVerdi(AiidaTestCase):
    """Tests for `verdi run`."""

    def setUp(self):
        super(TestVerdi, self).setUp()
        self.cli_runner = CliRunner()

    def test_verdi_version(self):
        """Regression test for #2238: verify that `verdi --version` prints the current version"""
        result = self.cli_runner.invoke(cmd_verdi.verdi, ['--version'])
        self.assertIsNone(result.exception, result.output)
        self.assertIn(get_version(), result.output)

    def test_verdi_with_empty_profile_list(self):
        # pylint: disable=protected-access
        """Test for #2424: verify that verdi remains operable even if profile list is empty"""
        from aiida.manage.configuration import CONFIG

        # Run verdi command with updated CONFIG featuring an empty profile list
        config_dict = dict(CONFIG._dictionary)
        CONFIG._dictionary[CONFIG.KEY_PROFILES] = {}
        result = self.cli_runner.invoke(cmd_verdi.verdi, [])
        self.assertIsNone(result.exception, result.output)

        # Restore original CONFIG contents
        CONFIG._dictionary = config_dict
