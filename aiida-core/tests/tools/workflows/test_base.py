###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for WorkflowTools"""

import pytest

from aiida.common.exceptions import LoadingEntryPointError
from aiida.orm import WorkChainNode
from aiida.tools.workflows import WorkflowTools

WORKFLOW_ENTRY_POINT_NAME = 'core.arithmetic.multiply_add'


class TestWorkflowTools(WorkflowTools):
    instances = 0

    def __init__(self, node):
        super().__init__(node)
        type(self).instances += 1

    def get_node(self):
        """Return the bound node."""
        return self._node


@pytest.fixture
def workflow_tools_entry_point(entry_points):
    """Register a workflow tools entry point for a built-in workflow plugin."""
    entry_points.add(TestWorkflowTools, f'aiida.tools.workflows:{WORKFLOW_ENTRY_POINT_NAME}')
    return TestWorkflowTools


def test_load_workflow_tools_entry_point(workflow_tools_entry_point):
    """Test loading tools for the built-in multiply-add work chain."""
    TestWorkflowTools.instances = 0
    node = WorkChainNode(process_type=f'aiida.workflows:{WORKFLOW_ENTRY_POINT_NAME}')
    assert isinstance(node.tools, workflow_tools_entry_point)
    assert node.tools.get_node() == node


def test_workflow_tools_cached(workflow_tools_entry_point):
    """Test that workflow tools are instantiated only once per node."""
    TestWorkflowTools.instances = 0
    node = WorkChainNode(process_type=f'aiida.workflows:{WORKFLOW_ENTRY_POINT_NAME}')

    first = node.tools
    second = node.tools

    assert first is second
    assert TestWorkflowTools.instances == 1


def test_fallback_workflow_tools():
    """Test fallback tools for the built-in multiply-add work chain."""
    node = WorkChainNode(process_type=f'aiida.workflows:{WORKFLOW_ENTRY_POINT_NAME}')
    assert isinstance(node.tools, WorkflowTools)


def test_fallback_workflow_tools_on_loading_error(monkeypatch, caplog):
    """Test fallback tools when the workflow tools entry point fails to load."""
    from aiida.plugins import entry_point as entry_point_module

    def raise_loading_entry_point_error(*_, **__):
        raise LoadingEntryPointError('broken tools entry point')

    monkeypatch.setattr(entry_point_module, 'load_entry_point', raise_loading_entry_point_error)

    node = WorkChainNode(process_type=f'aiida.workflows:{WORKFLOW_ENTRY_POINT_NAME}')

    assert isinstance(node.tools, WorkflowTools)
    assert f'could not load the workflow tools entry point {WORKFLOW_ENTRY_POINT_NAME}' in caplog.text


def test_default_workflow_tools_without_process_type():
    """Test that workflow tools fall back to `WorkflowTools` without a process type."""
    from aiida.tools.workflows import WorkflowTools

    node = WorkChainNode()
    assert isinstance(node.tools, WorkflowTools)


def test_default_workflow_tools_with_invalid_process_type():
    """Test that workflow tools fall back to `WorkflowTools` for invalid process types."""
    from aiida.tools.workflows import WorkflowTools

    node = WorkChainNode(process_type='invalid')
    assert isinstance(node.tools, WorkflowTools)
