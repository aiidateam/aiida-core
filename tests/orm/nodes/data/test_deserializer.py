###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.orm.nodes.data.deserializer`."""

import pytest

from aiida import orm
from aiida.orm.nodes.data.deserializer import deserialize_to_raw_python_data


def test_value_bearing_node_returns_its_value():
    assert deserialize_to_raw_python_data(orm.Int(5).store()) == 5


def test_list_node_deserialized_through_registry():
    assert deserialize_to_raw_python_data(orm.List(list=[1, 2, 3]).store()) == [1, 2, 3]


def test_dict_node_deserialized_through_registry():
    assert deserialize_to_raw_python_data(orm.Dict(dict={'a': 1}).store()) == {'a': 1}


def test_nested_mapping_is_walked_recursively():
    data = {'x': orm.Int(1).store(), 'y': {'z': orm.Str('s').store()}}
    assert deserialize_to_raw_python_data(data) == {'x': 1, 'y': {'z': 's'}}


def test_dry_run_returns_none_for_value_leaves():
    assert deserialize_to_raw_python_data(orm.Int(5).store(), dry_run=True) is None


def test_unknown_node_without_value_raises():
    node = orm.FolderData().store()
    with pytest.raises(ValueError, match='cannot deserialize an AiiDA data node'):
        deserialize_to_raw_python_data(node)
