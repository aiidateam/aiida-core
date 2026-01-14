###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for WorkflowTools"""

from aiida.orm import WorkChainNode


class MockWorkflow: ...


class MockWorkflowTools:
    def __init__(self, node):
        self._node = node


def test_mock_workflow_tools(entry_points):
    """Test if the workflow tools is correctly loaded from the entry point."""
    entry_points.add(MockWorkflow, 'aiida.workflows:MockWorkflow')
    entry_points.add(MockWorkflowTools, 'aiida.tools.workflows:MockWorkflow')
    node = WorkChainNode(process_type='aiida.workflows:MockWorkflow')
    assert isinstance(node.tools, MockWorkflowTools)
    assert node.tools._node == node


def test_fallback_workflow_tools(entry_points, generate_work_chain):
    """Test if the workflow tools is falling back to `WorkflowTools` if it cannot be loaded from entry point."""
    from aiida.tools.workflows import WorkflowTools

    entry_points.add(MockWorkflow, 'aiida.workflows:MockWorkflow')
    node = WorkChainNode(process_type='aiida.workflows:MockWorkflow')
    assert isinstance(node.tools, WorkflowTools)
    assert node.tools._node == node
