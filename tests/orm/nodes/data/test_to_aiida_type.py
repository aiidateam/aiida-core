###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test the :meth:`aiida.orm.data.base.to_aiida_type` serializer and its inverse."""

import numpy
import pytest

from aiida import orm
from aiida.common.links import LinkType


@pytest.mark.parametrize(
    'expected_type, value',
    (
        (orm.Bool, True),
        (orm.Dict, {'foo': 'bar'}),
        (orm.Float, 5.0),
        (orm.Int, 5),
        (orm.List, [0, 1, 2]),
        (orm.Str, 'test-string'),
        (orm.EnumData, LinkType.RETURN),
        (orm.ArrayData, numpy.array([[0, 0, 0], [1, 1, 1]])),
    ),
)
def test_to_aiida_type(expected_type, value):
    """Test the ``to_aiida_type`` dispatch."""
    converted = orm.to_aiida_type(value)
    assert isinstance(converted, expected_type)
    if expected_type is orm.ArrayData:
        assert converted.get_array().all() == value.all()
    else:
        assert converted == value


@pytest.mark.parametrize(
    'value',
    (
        True,
        {'foo': 'bar'},
        5.0,
        5,
        [0, 1, 2],
        'test-string',
        LinkType.RETURN,
    ),
)
def test_from_aiida_type_reads_back_what_to_aiida_type_stored(value):
    """The two dispatches are inverses, so a value survives the round trip as itself.

    The type is asserted as well as the value, since a node compares equal to what it holds and would satisfy
    the comparison alone.
    """
    read = orm.from_aiida_type(orm.to_aiida_type(value))

    assert read == value
    assert type(read) is type(value)


def test_from_aiida_type_hands_back_a_node_it_knows_nothing_about():
    """A port annotated with a ``Data`` subclass asks for the node, so an unregistered one is handed back."""
    node = orm.FolderData()

    assert orm.from_aiida_type(node) is node
