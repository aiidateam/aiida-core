# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi status`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_status


class TestVerdiStatus(AiidaTestCase):
    """Tests for `verdi rehash`."""

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_status_1(self):
        """Check running the command."""
        options = []
        result = self.cli_runner.invoke(cmd_status.verdi_status, options)
        self.assertClickResultNoException(result)
        self.assertTrue(result.exit_code == 0)
