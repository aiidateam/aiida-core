# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for common command line utilities."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.orm import Code
from aiida.orm import CalculationNode, CalcFunctionNode


class TestCommonUtilities(AiidaTestCase):
    """Tests for common command line utilities."""

    def test_get_node_summary(self):
        """Test the `get_node_summary` utility."""
        from aiida.cmdline.utils.common import get_node_summary

        computer_label = self.computer.name  # pylint: disable=no-member
        code_label = 'test_code'

        code = Code(
            input_plugin_name='arithmetic.add',
            remote_computer_exec=[self.computer, '/remote/abs/path'],
        )
        code.label = code_label
        code.store()

        node = CalculationNode()
        node.computer = self.computer
        node.add_incoming(code, link_type=LinkType.INPUT_CALC, link_label='code')
        node.store()

        summary = get_node_summary(node)
        self.assertIn(node.uuid, summary)
        self.assertIn(code_label, summary)
        self.assertIn(computer_label, summary)

    def test_get_process_function_report(self):
        """Test the `get_process_function_report` utility."""
        from aiida.cmdline.utils.common import get_process_function_report

        warning = 'You have been warned'

        node = CalcFunctionNode()
        node.store()

        # Add a log message through the logger
        node.logger.warning(warning)

        self.assertIn(warning, get_process_function_report(node))
