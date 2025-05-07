###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.nodes.data.array.array` module."""

import numpy
import pytest

from aiida.orm import ArrayData, load_node


def test_read_stored():
    """Test reading an array from an ``ArrayData`` after storing and loading it."""
    array = numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
    node = ArrayData()
    node.set_array('array', array)

    assert numpy.array_equal(node.get_array('array'), array)

    node.store()
    assert numpy.array_equal(node.get_array('array'), array)

    loaded = load_node(node.uuid)
    assert numpy.array_equal(loaded.get_array('array'), array)


def test_constructor():
    """Test the various construction options."""
    node = ArrayData()
    assert node.get_arraynames() == []

    arrays = numpy.array([1, 2])
    node = ArrayData(arrays)
    assert node.get_arraynames() == [ArrayData.default_array_name]
    assert (node.get_array(ArrayData.default_array_name) == arrays).all()

    arrays = {'a': numpy.array([1, 2]), 'b': numpy.array([3, 4])}
    node = ArrayData(arrays)
    assert sorted(node.get_arraynames()) == ['a', 'b']
    assert (node.get_array('a') == arrays['a']).all()
    assert (node.get_array('b') == arrays['b']).all()


def test_get_array():
    """Test :meth:`aiida.orm.nodes.data.array.array.ArrayData:get_array`."""
    node = ArrayData()
    with pytest.raises(ValueError, match='`name` not specified but the node contains no arrays.'):
        node.get_array()

    node = ArrayData({'a': numpy.array([]), 'b': numpy.array([])})
    with pytest.raises(ValueError, match='`name` not specified but the node contains multiple arrays.'):
        node.get_array()

    node = ArrayData({'a': numpy.array([1, 2])})
    assert (node.get_array() == numpy.array([1, 2])).all()

    node = ArrayData(numpy.array([1, 2]))
    assert (node.get_array() == numpy.array([1, 2])).all()
