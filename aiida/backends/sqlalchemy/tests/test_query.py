# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from six.moves import range, zip

from aiida.backends.testbase import AiidaTestCase


class TestQueryBuilderSQLA(AiidaTestCase):
    def test_clsf_sqla(self):
        from aiida.orm import Group, User, Computer, Node, Data
        from aiida.orm import ProcessNode
        from aiida.backends.sqlalchemy.models.node import DbNode
        from aiida.backends.sqlalchemy.models.group import DbGroup
        from aiida.backends.sqlalchemy.models.user import DbUser
        from aiida.backends.sqlalchemy.models.computer import DbComputer

        from aiida.orm.querybuilder import QueryBuilder

        qb = QueryBuilder()
        for AiidaCls, ORMCls in zip(
                (Group, User, Computer, Node, Data, ProcessNode),
                (DbGroup, DbUser, DbComputer, DbNode, DbNode, DbNode)):
            cls, classifiers = qb._get_ormclass(AiidaCls, None)

            self.assertEqual(cls, ORMCls)


class QueryBuilderLimitOffsetsTestSQLA(AiidaTestCase):

    def test_ordering_limits_offsets_of_results_for_SQLA(self):
        from aiida.orm import Node, Data
        from aiida.orm.querybuilder import QueryBuilder
        # Creating 10 nodes with an attribute that can be ordered
        for i in range(10):
            n = Data()
            n.set_attribute('foo', i)
            n.store()
        qb = QueryBuilder().append(
            Node, project='attributes.foo'
        ).order_by(
            {Node: {'attributes.foo': {'cast': 'i'}}}
        )
        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(10)))

        # Now applying an offset:
        qb.offset(5)
        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(5, 10)))

        # Now also applying a limit:
        qb.limit(3)
        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(5, 8)))
