# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for cif related functions."""
import numpy
import pytest

from aiida.manage.manager import get_manager
from aiida.orm import load_node, ArrayData


@pytest.mark.usefixtures('clear_database_before_test')
def test_read_stored():
    """Test the `parse_formula` utility function."""
    array = numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
    node = ArrayData()
    node.set_array('array', array)

    assert numpy.array_equal(node.get_array('array'), array)

    node.store()
    assert numpy.array_equal(node.get_array('array'), array)

    loaded = load_node(node.uuid)
    assert numpy.array_equal(loaded.get_array('array'), array)

    # Now pack all the files in the repository
    container = get_manager().get_profile().get_repository_container()
    container.pack_all_loose()

    loaded = load_node(node.uuid)
    assert numpy.array_equal(loaded.get_array('array'), array)
