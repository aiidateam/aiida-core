###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.cmdline.utils.common` module."""

from aiida.cmdline.utils import common
from aiida.common import LinkType
from aiida.engine import Process, calcfunction
from aiida.orm import CalcFunctionNode, CalculationNode, WorkflowNode


def test_get_node_summary(aiida_code_installed):
    """Test the ``get_node_summary`` utility."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    node = CalculationNode()
    node.computer = code.computer
    node.base.links.add_incoming(code, link_type=LinkType.INPUT_CALC, link_label='code')
    node.store()

    summary = common.get_node_summary(node)
    assert node.uuid in summary
    assert node.computer.label in summary


def test_get_node_info_multiple_call_links():
    """Test the ``get_node_info`` utility.

    Regression test for #2868:
        Verify that all `CALL` links are included in the formatted string even if link labels are identical.
    """
    workflow = WorkflowNode().store()
    node_one = CalculationNode()
    node_two = CalculationNode()

    node_one.base.links.add_incoming(workflow, link_type=LinkType.CALL_CALC, link_label='CALL_IDENTICAL')
    node_two.base.links.add_incoming(workflow, link_type=LinkType.CALL_CALC, link_label='CALL_IDENTICAL')
    node_one.store()
    node_two.store()

    node_info = common.get_node_info(workflow)
    assert 'CALL_IDENTICAL' in node_info
    assert str(node_one.pk) in node_info
    assert str(node_two.pk) in node_info


def test_get_process_function_report():
    """Test the ``get_process_function_report`` utility."""
    warning = 'You have been warned'
    node = CalcFunctionNode()
    node.store()

    node.logger.warning(warning)
    assert warning in common.get_process_function_report(node)


def test_print_process_info():
    """Test the ``print_process_info`` method."""

    class TestProcessWithoutDocstring(Process):
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

    @calcfunction
    def test_without_docstring():
        pass

    @calcfunction
    def test_with_docstring():
        """Some docstring."""

    # We are just checking that the command does not except
    common.print_process_info(TestProcessWithoutDocstring)
    common.print_process_info(TestProcessWithDocstring)
    common.print_process_info(test_without_docstring)
    common.print_process_info(test_with_docstring)
