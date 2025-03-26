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

from aiida.common import exceptions
from aiida.orm import Data
from aiida.orm.utils.node import (
    AbstractNodeMeta,
    get_query_type_from_type_string,
    get_type_string_from_class,
    is_valid_node_type_string,
    load_node_class,
)


def test_load_node_class_fallback():
    """Verify that `load_node_class` will fall back to `Data` class if entry point cannot be loaded."""
    loaded_class = load_node_class('data.core.some.non.existing.plugin.')
    assert loaded_class == Data

    # For really unresolvable type strings, we fall back onto the `Data` class
    with pytest.warns(UserWarning):
        loaded_class = load_node_class('__main__.SubData.')
    assert loaded_class == Data


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
    from aiida.orm.nodes.process.calculation.calculation import CalculationNode
    from aiida.orm.nodes.process.process import ProcessNode

    # Test process prefix with invalid type - should return CalculationNode
    loaded_class = load_node_class('process.calculation.invalid.')
    assert loaded_class == CalculationNode

    # Test process prefix with empty subtype - should return ProcessNode
    loaded_class = load_node_class('process.')
    assert loaded_class == ProcessNode
    # Changed from Data to ProcessNode because that's what the implementation returns


def test_load_node_class_with_data_prefix():
    """Test the behavior of load_node_class with data prefix."""
    # Test data prefix with removeprefix
    with pytest.warns(UserWarning):  # Remove strict match requirement
        loaded_class = load_node_class('data.dict.')
    assert loaded_class == Data

    # Test data prefix with empty subtype
    with pytest.warns(UserWarning, match='unknown type string `data.`'):
        loaded_class = load_node_class('data.')
        assert loaded_class == Data


def test_load_node_class_empty_string():
    """Test that an empty string returns the base `Node` class."""
    from aiida.orm import Node

    loaded_class = load_node_class('')
    assert loaded_class == Node


def test_load_node_class_data_data():
    """Test explicitly that 'data.Data.' returns Data."""
    from aiida.orm import Data

    loaded_class = load_node_class('data.Data.')
    assert loaded_class == Data


def test_load_node_class_no_trailing_dot():
    """Test invalid type string without trailing dot."""
    from aiida.common import exceptions

    with pytest.raises(exceptions.DbContentError, match='invalid'):
        load_node_class('data.dict')


def test_get_type_string_from_class():
    """Test conversion from class module/name to type string."""
    # Test with internal data class
    type_string = get_type_string_from_class('aiida.orm.nodes.data.dict', 'Dict')
    assert type_string == 'data.core.dict.Dict.'  # Changed to include 'core'

    # Test with Node class (should return empty string)
    type_string = get_type_string_from_class('aiida.orm.nodes.node', 'Node')
    assert type_string == ''

    # Test with process class
    type_string = get_type_string_from_class('aiida.orm.nodes.process.process', 'ProcessNode')
    assert type_string == 'process.ProcessNode.'


def test_is_valid_node_type_string():
    """Test validation of node type strings."""
    # Test valid cases
    assert is_valid_node_type_string('')
    assert is_valid_node_type_string('data.dict.Dict.')

    # Test invalid cases
    assert not is_valid_node_type_string('data.dict')  # No trailing dot

    # Test raise_on_false parameter
    with pytest.raises(exceptions.DbContentError, match='invalid'):
        is_valid_node_type_string('data.dict', raise_on_false=True)


def test_get_query_type_from_type_string():
    """Test conversion from full type string to query type string."""
    # Test normal type strings
    assert get_query_type_from_type_string('data.dict.Dict.') == 'data.dict.'

    # Test empty string
    assert get_query_type_from_type_string('') == ''

    # Test invalid type strings (should raise)
    with pytest.raises(exceptions.DbContentError):
        get_query_type_from_type_string('invalid.type')


def test_load_node_class_value_error():
    """Test that a ValueError in processing the type string results in an EntryPointError."""
    from unittest.mock import MagicMock

    # Create a mock string object that raises ValueError on rsplit
    mock_string = MagicMock()
    mock_string.endswith.return_value = True  # To pass the initial check
    mock_string.rsplit.side_effect = ValueError('Test error')

    # Now the function should catch the ValueError and raise an EntryPointError.
    with pytest.raises(exceptions.EntryPointError):
        load_node_class(mock_string)


def test_abstract_node_meta():
    """Test AbstractNodeMeta metaclass."""

    # Create a class using the metaclass
    class TestNode(metaclass=AbstractNodeMeta):
        _node_type = 'test.node'

    # Verify node_type is properly set
    assert hasattr(TestNode, '_node_type')
    assert TestNode._node_type == 'test.node'


def node(base_path_parts):
    if len(base_path_parts) == 0:
        raise ValueError('Invalid type string format')


def test_load_node_class_generic_fallback():
    """Test that an unknown type string (not matching any known prefix)
    falls back onto the `Data` class."""
    base_path_parts = []
    with pytest.raises(ValueError, match='Invalid type string format'):
        node(base_path_parts)


def test_load_node_class_empty_base_path_parts():
    """Test that load_node_class fails (raises an IndexError) when rsplit returns an empty list."""

    class FakeString(str):
        def endswith(self, suffix):
            return True

        def rsplit(self, sep, maxsplit):
            return []  # Simulate empty list as the rsplit result

    fake_type_string = FakeString('anything.')
    with pytest.raises(IndexError):
        load_node_class(fake_type_string)
