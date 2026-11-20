###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Leaf element contracts for container annotations."""

import pytest

from aiida.engine.processes.graphs.shapes import LeafShape, dump_shape, load_shape, shape_for_annotation
from aiida.orm import DataList, Int
from aiida.orm import Dict as DataDict


def test_plain_list_element() -> None:
    """Plain containers keep runtime types and record the member contract."""
    shape = shape_for_annotation(list[int])
    assert isinstance(shape, LeafShape)
    assert shape.types == (list,)
    assert shape.element == LeafShape(types=(int,))


def test_data_list_element() -> None:
    """Node members map to owned storage with the member contract preserved."""
    shape = shape_for_annotation(list[Int])
    assert isinstance(shape, LeafShape)
    assert shape.types == (DataList,)
    assert shape.element == LeafShape(types=(Int,))


def test_nested_dict_element_roundtrip() -> None:
    """Nested members recurse and survive serialization."""
    shape = shape_for_annotation(dict[str, list[int]])
    assert isinstance(shape, LeafShape)
    assert shape.types == (dict,)
    assert shape.element == LeafShape(types=(list,), element=LeafShape(types=(int,)))
    assert load_shape(dump_shape(shape)) == shape


def test_missing_element_loads_none() -> None:
    """Shapes serialized before elements existed load without one."""
    dumped = dump_shape(LeafShape(types=(int,)))
    assert 'element' not in dumped
    assert load_shape(dumped) == LeafShape(types=(int,), element=None)


@pytest.mark.parametrize(
    ('annotation', 'expected_types'),
    [(list, (list,)), (dict, (dict,)), (int, (int,)), (DataDict, (DataDict,))],
    ids=['bare-list', 'bare-dict', 'scalar', 'data-dict'],
)
def test_no_element_without_member(annotation: object, expected_types: tuple[type, ...]) -> None:
    """Declarations without a member type declare no element contract."""
    shape = shape_for_annotation(annotation)
    assert isinstance(shape, LeafShape)
    assert shape.types == expected_types
    assert shape.element is None
