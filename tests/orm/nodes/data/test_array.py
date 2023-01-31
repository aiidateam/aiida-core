# -*- coding: utf-8 -*-
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
