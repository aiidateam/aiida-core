###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for CalculationTools"""


class MockCalculation: ...


class MockCalculationTools:
    def __init__(self, node):
        self._node = node


def test_mock_calculation_tools(entry_points, generate_calcjob_node):
    """Test if the calculation tools is correctly loaded from the entry point."""
    entry_points.add(MockCalculation, 'aiida.calculations:MockCalculation')
    entry_points.add(MockCalculationTools, 'aiida.tools.calculations:MockCalculation')
    node = generate_calcjob_node(entry_point='aiida.calculations:MockCalculation')
    assert isinstance(node.tools, MockCalculationTools)
    assert node.tools._node == node


def test_fallback_calculation_tools(entry_points, generate_calcjob_node):
    """Test if the calculation tools is falling back to `CalculationTools` if it cannot be loaded from entry point."""
    from aiida.tools.calculations import CalculationTools

    entry_points.add(MockCalculation, 'aiida.calculations:MockCalculation')
    node = generate_calcjob_node(entry_point='aiida.calculations:MockCalculation')
    assert isinstance(node.tools, CalculationTools)
    assert node.tools._node == node
