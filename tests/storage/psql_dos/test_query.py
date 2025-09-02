###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for generic queries and unit tests for QueryBuilder parameter limit fixes."""

from pathlib import Path

import pytest

from aiida import orm
from aiida.orm import Computer, Data, Group, Node, ProcessNode, QueryBuilder, User
from aiida.tools.archive import import_archive


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


@pytest.mark.requires_psql
# @pytest.mark.usefixtures('aiida_profile_clean')
class TestQueryBuilderParameterLimits:
    """Test QueryBuilder handles large parameter lists correctly."""

    @classmethod
    def setup_class(cls):
        """Import the 100k node archive once for all tests."""
        cls.num_nodes = 100_000
        archive_path = Path(__file__).parent / 'data' / f'{int(cls.num_nodes/1000)}k-int-nodes-2.7.1.post0.aiida'
        import_archive(archive_path)

        # Cache PKs on the class for reuse
        qb = orm.QueryBuilder()
        qb.append(orm.Int, project='uuid')
        cls.all_uuids = qb.all(flat=True)
        assert len(cls.all_uuids) == cls.num_nodes

    def test_large_in_filter_batching(self):
        """Test that large IN filters are automatically batched to avoid parameter limits."""
        # Use all 50k nodes - this would fail without batching
        qb = orm.QueryBuilder()
        qb.append(orm.Node, filters={'uuid': {'in': self.all_uuids}})
        results = qb.all(flat=True)

        assert len(results) == self.num_nodes

    def test_jsonb_large_in_filter(self):
        """Test large IN filters on JSONB attributes fields."""
        # Get attribute values from nodes to create a large list for JSONB filtering
        qb = orm.QueryBuilder()
        qb.append(orm.Int, project='attributes.value')
        sample_values = [v for (v,) in qb.all() if v is not None]
        
        if sample_values:
            # Create a very large list by replicating values to exceed 100k
            large_value_list = sample_values * (100000 // len(sample_values) + 1)
            large_value_list = large_value_list[:100000]  # Use exactly 100k values
            
            # This tests the JSONB batching logic in get_filter_expr_from_jsonb
            qb = orm.QueryBuilder()
            qb.append(orm.Int, filters={'attributes.value': {'in': large_value_list}})
            results = qb.all(flat=True)
            
            # Should not raise parameter limit error
            breakpoint()
            assert len(results) >= 0
