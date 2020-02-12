# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for common command line utilities."""

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType


class TestCommonUtilities(AiidaTestCase):
    """Tests for common command line utilities."""

    def test_get_node_summary(self):
        """Test the `get_node_summary` utility."""
        from aiida.cmdline.utils.common import get_node_summary

        computer_label = self.computer.name  # pylint: disable=no-member

        code = orm.Code(
            input_plugin_name='arithmetic.add',
            remote_computer_exec=[self.computer, '/remote/abs/path'],
        )
        code.store()

        node = orm.CalculationNode()
        node.computer = self.computer
        node.add_incoming(code, link_type=LinkType.INPUT_CALC, link_label='code')
        node.store()

        summary = get_node_summary(node)
        self.assertIn(node.uuid, summary)
        self.assertIn(computer_label, summary)

    def test_get_node_info_multiple_call_links(self):
        """Test the `get_node_info` utility.

        Regression test for #2868:
            Verify that all `CALL` links are included in the formatted string even if link labels are identical.
        """
        from aiida.cmdline.utils.common import get_node_info

        workflow = orm.WorkflowNode().store()
        node_one = orm.CalculationNode()
        node_two = orm.CalculationNode()

        node_one.add_incoming(workflow, link_type=LinkType.CALL_CALC, link_label='CALL_IDENTICAL')
        node_two.add_incoming(workflow, link_type=LinkType.CALL_CALC, link_label='CALL_IDENTICAL')
        node_one.store()
        node_two.store()

        node_info = get_node_info(workflow)
        self.assertTrue('CALL_IDENTICAL' in node_info)
        self.assertTrue(str(node_one.pk) in node_info)
        self.assertTrue(str(node_two.pk) in node_info)

    def test_get_process_function_report(self):
        """Test the `get_process_function_report` utility."""
        from aiida.cmdline.utils.common import get_process_function_report

        warning = 'You have been warned'

        node = orm.CalcFunctionNode()
        node.store()

        # Add a log message through the logger
        node.logger.warning(warning)

        self.assertIn(warning, get_process_function_report(node))

    def test_print_process_info(self):
        """Test the `print_process_info` method."""
        from aiida.cmdline.utils.common import print_process_info
        from aiida.common.utils import Capturing
        from aiida.engine import Process

        class TestProcessWithoutDocstring(Process):
            # pylint: disable=missing-docstring

            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input('some_input')

        class TestProcessWithDocstring(Process):
            """Some docstring."""

            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input('some_input')

        # We are just checking that the command does not except
        with Capturing():
            print_process_info(TestProcessWithoutDocstring)
            print_process_info(TestProcessWithDocstring)
