###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regression tests for data queries and container behavior at provenance boundaries."""

import pytest

from aiida.common.exceptions import IncompatibleStorageSchema
from aiida.orm import (
    CalcJobNode,
    Container,
    Data,
    DataDict,
    DataList,
    Dict,
    Int,
    QueryBuilder,
    Str,
)


def test_load_node_class():
    """Type-string resolution keeps legacy strings."""
    from aiida.orm.utils.node import load_node_class

    assert load_node_class(DataList.class_node_type) is DataList
    assert load_node_class(DataDict.class_node_type) is DataDict
    assert load_node_class('data.Data.') is Data
    assert load_node_class('data.core.int.Int.') is Int
    # The removed ``Code`` plugin still raises instead of silently falling back.
    with pytest.raises(IncompatibleStorageSchema):
        load_node_class('data.core.code.Code.')
    # Unknown ``data.`` type strings keep the legacy ``Data`` fallback without warning.
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter('error')
        assert load_node_class('data.core.unknown.Unknown.') is Data


def test_querybuilder_data_includes_containers(aiida_profile_clean):
    """``Data`` matches all data nodes and ``Container`` matches only containers."""
    Int(1).store()
    DataList([Int(2)]).store()
    DataDict({'a': Int(3)}).store()

    # Owned children are ``DbNode`` rows too, so they match data queries as well: one standalone ``Int`` plus
    # two containers plus their two owned ``Int`` children.
    assert QueryBuilder().append(Data).count() == 5
    assert QueryBuilder().append(Container).count() == 2
    assert QueryBuilder().append(DataList).count() == 1
    assert QueryBuilder().append(DataDict).count() == 1
    assert QueryBuilder().append(DataList, subclassing=False).count() == 1
    assert {type(node) for (node,) in QueryBuilder().append(Data, project='*').all()} == {
        Int,
        DataList,
        DataDict,
    }
    # Stored type strings are unchanged legacy identifiers.
    assert DataList.class_node_type == 'data.core.data_list.DataList.'
    assert DataDict.class_node_type == 'data.core.data_dict.DataDict.'
    assert Data.class_node_type == 'data.Data.'


def test_querybuilder_data_subclass_excludes_containers(aiida_profile_clean):
    """A ``Data`` subclass query never returns containers sharing the ``data.`` prefix."""
    Int(1).store()
    DataList([Int(2)]).store()

    # The owned ``Int`` child matches too, but no container ever matches a ``Data`` subclass query.
    assert QueryBuilder().append(Int).count() == 2
    assert {type(node) for (node,) in QueryBuilder().append(Int, project='*').all()} == {Int}
    assert QueryBuilder().append(Str).count() == 0
    assert QueryBuilder().append(Dict).count() == 0


def test_links_accept_containers():
    """Provenance link validation treats containers like data at the boundary."""
    from aiida.common.links import LinkType
    from aiida.orm.utils.links import validate_link

    source = CalcJobNode()
    target = DataList([Int(1)])
    validate_link(source, target, LinkType.CREATE, 'result')
    validate_link(target, source, LinkType.INPUT_CALC, 'input')
