# -*- coding: utf-8 -*-
"""
Tests for nodes, attributes and links
"""

from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.backends.tests.nodes import *


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestDataNodeSQLA(SqlAlchemyTests, TestDataNode):
    """
    These tests check the features of Data nodes that differ from the base Node
    """
    pass


class TestTransitiveNoLoopsSQLA(SqlAlchemyTests, TestTransitiveNoLoops):
    """
    Test the creation of the transitive closure table
    """
    pass


class TestTransitiveClosureDeletionSQLA(SqlAlchemyTests,
                                        TestTransitiveClosureDeletion):
    """
    Test the creation of the transitive closure table
    """
    def test_creation_and_deletion(self):
        from aiida.backends.sqlalchemy.models.node import DbLink  # Direct links
        from aiida.backends.sqlalchemy.models.node import DbPath # The transitive closure table
        from aiida.orm.node import Node

        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()
        n5 = Node().store()
        n6 = Node().store()
        n7 = Node().store()
        n8 = Node().store()
        n9 = Node().store()

        # I create a strange graph, inserting links in a order
        # such that I often have to create the transitive closure
        # between two graphs
        n3.add_link_from(n2)
        n2.add_link_from(n1)
        n5.add_link_from(n3)
        n5.add_link_from(n4)
        n4.add_link_from(n2)

        n7.add_link_from(n6)
        n8.add_link_from(n7)

        # Yet, no links from 1 to 8
        self.assertEquals(
            DbPath.query.filter(DbPath.parent == n1.dbnode,
                                DbPath.child == n8.dbnode).distinct().count(),
            0)

        n6.add_link_from(n5)
        # Yet, now 2 links from 1 to 8
        self.assertEquals(
            DbPath.query.filter(DbPath.parent == n1.dbnode,
                                DbPath.child == n8.dbnode).distinct().count(),
            2)

        n7.add_link_from(n9)
        # Still two links...
        self.assertEquals(
            DbPath.query.filter(DbPath.parent == n1.dbnode,
                                DbPath.child == n8.dbnode).distinct().count(),
            2)

        n9.add_link_from(n6)
        # And now there should be 4 nodes
        self.assertEquals(
            DbPath.query.filter(DbPath.parent == n1.dbnode,
                                DbPath.child == n8.dbnode).distinct().count(),
            4)

        ### I start deleting now

        # I cut one branch below: I should loose 2 links
        DbLink.query.filter(DbLink.input == n6.dbnode,
                            DbLink.output == n9.dbnode).delete()
        self.assertEquals(
            DbPath.query.filter(DbPath.parent == n1.dbnode,
                                DbPath.child == n8.dbnode).distinct().count(),
            2)

        # I cut another branch above: I should loose one more link
        DbLink.query.filter(DbLink.input == n2.dbnode,
                            DbLink.output == n4.dbnode).delete()
        self.assertEquals(
            DbPath.query.filter(DbPath.parent == n1.dbnode,
                                DbPath.child == n8.dbnode).distinct().count(),
            1)

        # Another cut should delete all links
        DbLink.query.filter(DbLink.input == n3.dbnode,
                            DbLink.output == n5.dbnode).delete()

        self.assertEquals(
            DbPath.query.filter(DbPath.parent == n1.dbnode,
                                DbPath.child == n8.dbnode).distinct().count(),
            0)

        # But I did not delete everything! For instance, I can check
        # the following links
        self.assertEquals(
            DbPath.query.filter(DbPath.parent == n4.dbnode,
                                DbPath.child == n8.dbnode).distinct().count(),
            1)
        self.assertEquals(
            DbPath.query.filter(DbPath.parent == n5.dbnode,
                                DbPath.child == n7.dbnode).distinct().count(),
            1)

        # Finally, I reconnect in a different way the two graphs and
        # check that 1 and 8 are again connected
        n4.add_link_from(n3)
        self.assertEquals(
            DbPath.query.filter(DbPath.parent == n1.dbnode,
                                DbPath.child == n8.dbnode).distinct().count(),
            1)


class TestQueryWithAiidaObjectsSQLA(SqlAlchemyTests,
                                    TestQueryWithAiidaObjects):
    """
    Test if queries work properly also with aiida.orm.Node classes instead of
    aiida.backends.djsite.db.models.DbNode objects.
    """
    pass


class TestNodeBasicSQLA(SqlAlchemyTests, TestNodeBasic):
    """
    These tests check the basic features of nodes
    (setting of attributes, copying of files, ...)
    """
    def test_settings(self):
        """
        Test the settings table (similar to Attributes, but without the key.
        """
        from aiida.backends.sqlalchemy.models.settings import DbSetting
        from aiida.backends.sqlalchemy import session
        from pytz import UTC
        from aiida.utils import timezone
        from sqlalchemy.exc import IntegrityError

        DbSetting.set_value(key='pippo', value=[1, 2, 3])

        # s1 = DbSetting.objects.get(key='pippo')
        s1 = DbSetting.query.filter_by(key='pippo').first()

        self.assertEqual(s1.getvalue(), [1, 2, 3])

        s2 = DbSetting(key='pippo')
        s2.time = timezone.datetime.now(tz=UTC)
        with self.assertRaises(IntegrityError):
            with session.begin_nested():
                # same name...
                session.add(s2)

        # Should replace pippo
        DbSetting.set_value(key='pippo', value="a")
        s1 = DbSetting.query.filter_by(key='pippo').first()

        self.assertEqual(s1.getvalue(), "a")


class TestSubNodesAndLinksSQLA(SqlAlchemyTests, TestSubNodesAndLinks):
    """
    Test the proper functionality of the links cache, with different
    scenarios.
    """
    pass
