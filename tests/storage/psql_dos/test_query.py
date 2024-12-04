###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for generic queries."""

import pytest

from aiida.orm import Computer, Data, Group, Node, ProcessNode, QueryBuilder, User


def test_qb_clsf_sqla():
    """Test SQLA classifiers"""
    from aiida.orm.querybuilder import _get_ormclass

    for aiida_cls, orm_name in zip(
        (Group, User, Computer, Node, Data, ProcessNode), ('group', 'user', 'computer', 'node', 'node', 'node')
    ):
        cls, _ = _get_ormclass(aiida_cls, None)

        assert cls.value == orm_name


@pytest.mark.usefixtures('aiida_profile_clean')
def test_qb_ordering_limits_offsets_sqla():
    """Test ordering limits offsets of SQLA query results."""
    # Creating 10 nodes with an attribute that can be ordered
    for i in range(10):
        node = Data()
        node.base.attributes.set('foo', i)
        node.store()
    q_b = QueryBuilder().append(Node, project='attributes.foo').order_by({Node: {'attributes.foo': {'cast': 'i'}}})
    res = next(zip(*q_b.all()))
    assert res == tuple(range(10))

    # Now applying an offset:
    q_b.offset(5)
    res = next(zip(*q_b.all()))
    assert res == tuple(range(5, 10))

    # Now also applying a limit:
    q_b.limit(3)
    res = next(zip(*q_b.all()))
    assert res == tuple(range(5, 8))
