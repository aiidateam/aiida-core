# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for generic queries."""

from aiida.backends.testbase import AiidaTestCase


class TestQueryBuilderSQLA(AiidaTestCase):
    """Test QueryBuilder for SQLA objects."""

    def test_clsf_sqla(self):
        """Test SQLA classifiers"""
        from aiida.orm import Group, User, Computer, Node, Data
        from aiida.orm import ProcessNode
        from aiida.backends.sqlalchemy.models.node import DbNode
        from aiida.backends.sqlalchemy.models.group import DbGroup
        from aiida.backends.sqlalchemy.models.user import DbUser
        from aiida.backends.sqlalchemy.models.computer import DbComputer

        from aiida.orm.querybuilder import QueryBuilder

        q_b = QueryBuilder()
        for aiida_cls, orm_cls in zip((Group, User, Computer, Node, Data, ProcessNode),
                                      (DbGroup, DbUser, DbComputer, DbNode, DbNode, DbNode)):
            cls, _ = q_b._get_ormclass(aiida_cls, None)  # pylint: disable=protected-access

            self.assertEqual(cls, orm_cls)


class QueryBuilderLimitOffsetsTestSQLA(AiidaTestCase):
    """Test query builder limits."""

    def test_ordering_limits_offsets_sqla(self):
        """Test ordering limits offsets of SQLA query results."""
        from aiida.orm import Node, Data
        from aiida.orm.querybuilder import QueryBuilder
        # Creating 10 nodes with an attribute that can be ordered
        for i in range(10):
            node = Data()
            node.set_attribute('foo', i)
            node.store()
        q_b = QueryBuilder().append(Node, project='attributes.foo').order_by({Node: {'attributes.foo': {'cast': 'i'}}})
        res = next(zip(*q_b.all()))
        self.assertEqual(res, tuple(range(10)))

        # Now applying an offset:
        q_b.offset(5)
        res = next(zip(*q_b.all()))
        self.assertEqual(res, tuple(range(5, 10)))

        # Now also applying a limit:
        q_b.limit(3)
        res = next(zip(*q_b.all()))
        self.assertEqual(res, tuple(range(5, 8)))
