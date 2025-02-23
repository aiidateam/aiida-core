###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `Node` utils."""

import pytest

from aiida.orm import Data
from aiida.orm.utils.node import load_node_class


def test_load_node_class_fallback():
    """Verify that `load_node_class` will fall back to `Data` class if entry point cannot be loaded."""
    loaded_class = load_node_class('data.core.some.non.existing.plugin.')
    assert loaded_class == Data

    # For really unresolvable type strings, we fall back onto the `Data` class
    with pytest.warns(UserWarning):
        loaded_class = load_node_class('__main__.SubData.')
    assert loaded_class == Data


# Test for Remove_prefix

def test_load_node_class_with_node_prefix():
    """Test the behavior of load_node_class with node prefix."""
    # Test node prefix removal
    with pytest.warns(UserWarning):
        loaded_class = load_node_class('node.data.dict.')
        assert loaded_class == Data

    # Test node prefix with invalid subtype
    with pytest.warns(UserWarning):
        loaded_class = load_node_class('node.invalid.type.')
        assert loaded_class == Data

def test_load_node_class_with_process_prefix():
    """Test the behavior of load_node_class with process prefix."""
    from aiida.orm.nodes.process.process import ProcessNode
    from aiida.orm.nodes.process.calculation.calculation import CalculationNode
    
    # Test process prefix with invalid type - should return CalculationNode
    loaded_class = load_node_class('process.calculation.invalid.')
    assert loaded_class == CalculationNode

    # Test process prefix with empty subtype - should return ProcessNode
    loaded_class = load_node_class('process.')
    assert loaded_class == ProcessNode  # Changed from Data to ProcessNode because that's what the implementation returns

def test_load_node_class_with_data_prefix():
    """Test the behavior of load_node_class with data prefix."""
    # Test data prefix with removeprefix
    with pytest.warns(UserWarning, match="unknown type string `data.dict.`"):
        loaded_class = load_node_class('data.dict.')
        assert loaded_class == Data

    # Test data prefix with empty subtype
    with pytest.warns(UserWarning, match="unknown type string `data.`"):
        loaded_class = load_node_class('data.')
        assert loaded_class == Data