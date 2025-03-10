###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.nodes.data.array.xy` module."""

import numpy
import pytest

from aiida.common.exceptions import NotExistent
from aiida.orm import XyData, load_node


def test_read_stored():
    """Test reading an array from an ``XyData`` after storing and loading it."""
    x_array = numpy.array([1, 2])
    y_array = numpy.array([3, 4])
    node = XyData(x_array, y_array, x_name='x_name', x_units='x_unit', y_names='y_name', y_units='y_units')

    assert numpy.array_equal(node.get_x()[1], x_array)
    assert numpy.array_equal(node.get_y()[0][1], y_array)

    node.store()
    assert numpy.array_equal(node.get_x()[1], x_array)
    assert numpy.array_equal(node.get_y()[0][1], y_array)

    loaded = load_node(node.uuid)
    assert numpy.array_equal(loaded.get_x()[1], x_array)
    assert numpy.array_equal(loaded.get_y()[0][1], y_array)


def test_constructor():
    """Test the various construction options."""
    with pytest.raises(TypeError):
        node = XyData(numpy.array([1, 2]))

    node = XyData()

    with pytest.raises(NotExistent):
        node.get_x()

    with pytest.raises(NotExistent):
        node.get_y()

    x_array = numpy.array([1, 2])
    y_array = numpy.array([3, 4])
    node = XyData(x_array, y_array, x_name='x_name', x_units='x_unit', y_names='y_name', y_units='y_units')
    assert numpy.array_equal(node.get_x()[1], x_array)
    assert numpy.array_equal(node.get_y()[0][1], y_array)


def test_get_y_arraynames():
    """Test retrieving y array names."""
    x_array = numpy.array([1, 2])
    y_array1 = numpy.array([3, 4])
    y_array2 = numpy.array([5, 6])

    node = XyData()
    node.set_x(x_array, 'x_name', 'x_unit')
    node.set_y([y_array1, y_array2], ['y_name1', 'y_name2'], ['y_unit1', 'y_unit2'])

    y_names = node.get_y_arraynames()
    assert y_names == ['y_name1', 'y_name2']

    # Test when no y_array exists
    empty_node = XyData()
    with pytest.raises(NotExistent):
        empty_node.get_y_arraynames()

    # Test when y_array have inconsistent shapes
    invalid_y_array = numpy.array([3, 4, 5])

    invalid_node = XyData()
    invalid_node.set_x(x_array, 'x_name', 'x_unit')

    with pytest.raises(ValueError, match=r"y_array .* does not have the same shape as x_array!"):
        invalid_node.set_y([y_array1, invalid_y_array], ['y_name1', 'invalid_y_name'], ['y_unit1', 'invalid_y_unit'])
