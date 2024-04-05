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
