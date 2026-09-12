###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for CalculationTools"""

import pytest

from aiida.common.exceptions import LoadingEntryPointError
from aiida.tools.calculations import CalculationTools

CALCULATION_ENTRY_POINT_NAME = 'core.arithmetic.add'


class TestCalculationTools(CalculationTools):
    instances = 0

    def __init__(self, node):
        super().__init__(node)
        type(self).instances += 1

    def get_node(self):
        """Return the bound node."""
        return self._node


@pytest.fixture
def calculation_tools_entry_point(entry_points):
    """Register a calculation tools entry point for a built-in calculation plugin."""
    entry_points.add(TestCalculationTools, f'aiida.tools.calculations:{CALCULATION_ENTRY_POINT_NAME}')
    return TestCalculationTools


def test_load_calculation_tools_entry_point(calculation_tools_entry_point, generate_calcjob_node):
    """Test loading tools for the built-in arithmetic add calculation."""
    TestCalculationTools.instances = 0
    node = generate_calcjob_node(entry_point=f'aiida.calculations:{CALCULATION_ENTRY_POINT_NAME}')
    assert isinstance(node.tools, calculation_tools_entry_point)
    assert node.tools.get_node() == node


def test_calculation_tools_cached(calculation_tools_entry_point, generate_calcjob_node):
    """Test that calculation tools are instantiated only once per node."""
    TestCalculationTools.instances = 0
    node = generate_calcjob_node(entry_point=f'aiida.calculations:{CALCULATION_ENTRY_POINT_NAME}')

    first = node.tools
    second = node.tools

    assert first is second
    assert TestCalculationTools.instances == 1


def test_fallback_calculation_tools(generate_calcjob_node):
    """Test fallback tools for the built-in arithmetic add calculation."""
    node = generate_calcjob_node(entry_point=f'aiida.calculations:{CALCULATION_ENTRY_POINT_NAME}')
    assert isinstance(node.tools, CalculationTools)


def test_fallback_calculation_tools_on_loading_error(monkeypatch, generate_calcjob_node, caplog):
    """Test fallback tools when the calculation tools entry point fails to load."""
    from aiida.plugins import entry_point as entry_point_module

    # Create the node before monkeypatching, otherwise the patch also breaks
    # ``StorageFactory`` which calls ``load_entry_point`` during node creation.
    node = generate_calcjob_node(entry_point=f'aiida.calculations:{CALCULATION_ENTRY_POINT_NAME}')

    def raise_loading_entry_point_error(*_, **__):
        raise LoadingEntryPointError('broken tools entry point')

    monkeypatch.setattr(entry_point_module, 'load_entry_point', raise_loading_entry_point_error)

    assert isinstance(node.tools, CalculationTools)
    assert f'could not load the calculation tools entry point {CALCULATION_ENTRY_POINT_NAME}' in caplog.text


def test_default_calculation_tools_without_process_type(generate_calcjob_node):
    """Test that calculation tools fall back to `CalculationTools` without a process type."""
    from aiida.tools.calculations import CalculationTools

    node = generate_calcjob_node()
    assert isinstance(node.tools, CalculationTools)


def test_default_calculation_tools_with_invalid_process_type(generate_calcjob_node):
    """Test that calculation tools fall back to `CalculationTools` for invalid process types."""
    from aiida.tools.calculations import CalculationTools

    node = generate_calcjob_node(entry_point='invalid')
    assert isinstance(node.tools, CalculationTools)
