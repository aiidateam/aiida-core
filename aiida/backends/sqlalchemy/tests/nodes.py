# -*- coding: utf-8 -*-
"""
Tests for nodes, attributes and links
"""

from aiida.backends.testbase import AiidaTestCase
from aiida.orm.node import Node

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1"


class TestTransitiveClosureDeletionSQLA(AiidaTestCase):
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


class TestNodeBasicSQLA(AiidaTestCase):
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

    def test_load_nodes(self):
        """
        Test for load_node() function.
        """
        from aiida.orm import load_node
        from aiida.common.exceptions import NotExistent
        import aiida.backends.sqlalchemy

        a = Node()
        a.store()

        self.assertEquals(a.pk, load_node(node_id=a.pk).pk)
        self.assertEquals(a.pk, load_node(node_id=a.uuid).pk)
        self.assertEquals(a.pk, load_node(pk=a.pk).pk)
        self.assertEquals(a.pk, load_node(uuid=a.uuid).pk)

        try:
            aiida.backends.sqlalchemy.session.begin_nested()
            with self.assertRaises(ValueError):
                load_node(node_id=a.pk, pk=a.pk)
        finally:
            aiida.backends.sqlalchemy.session.rollback()

        try:
            aiida.backends.sqlalchemy.session.begin_nested()
            with self.assertRaises(ValueError):
                load_node(pk=a.pk, uuid=a.uuid)
        finally:
            aiida.backends.sqlalchemy.session.rollback()

        try:
            aiida.backends.sqlalchemy.session.begin_nested()
            with self.assertRaises(ValueError):
                load_node(pk=a.uuid)
        finally:
            aiida.backends.sqlalchemy.session.rollback()

        try:
            aiida.backends.sqlalchemy.session.begin_nested()
            with self.assertRaises(NotExistent):
                load_node(uuid=a.pk)
        finally:
            aiida.backends.sqlalchemy.session.rollback()

        try:
            aiida.backends.sqlalchemy.session.begin_nested()
            with self.assertRaises(ValueError):
                load_node()
        finally:
            aiida.backends.sqlalchemy.session.rollback()

    def test_multiple_node_creation(self):
        """
        This test checks that a node is not added automatically to the session
        (and subsequently committed) when a user is in the session.
        It tests the fix for the issue #234
        """
        from aiida.backends.sqlalchemy.models.node import DbNode
        from aiida.common.utils import get_new_uuid
        from aiida.backends.utils import get_automatic_user

        import aiida.backends.sqlalchemy

        # Get the automatic user
        user = get_automatic_user()
        # Create a new node but don't add it to the session
        node_uuid = get_new_uuid()
        DbNode(user=user, uuid=node_uuid, type=None)

        # Query the session before commit
        res = aiida.backends.sqlalchemy.session.query(DbNode.uuid).filter(
            DbNode.uuid == node_uuid).all()
        self.assertEqual(len(res), 0, "There should not be any nodes with this"
                                      "UUID in the session/DB.")

        # Commit the transaction
        aiida.backends.sqlalchemy.session.commit()

        # Check again that the node is not in the DB
        res = aiida.backends.sqlalchemy.session.query(DbNode.uuid).filter(
            DbNode.uuid == node_uuid).all()
        self.assertEqual(len(res), 0, "There should not be any nodes with this"
                                      "UUID in the session/DB.")

        # Get the automatic user
        user = get_automatic_user()
        # Create a new node but now add it to the session
        node_uuid = get_new_uuid()
        node = DbNode(user=user, uuid=node_uuid, type=None)
        aiida.backends.sqlalchemy.session.add(node)

        # Query the session before commit
        res = aiida.backends.sqlalchemy.session.query(DbNode.uuid).filter(
            DbNode.uuid == node_uuid).all()
        self.assertEqual(len(res), 1,
                         "There should be a node in the session/DB with the "
                         "UUID {}".format(node_uuid))

        # Commit the transaction
        aiida.backends.sqlalchemy.session.commit()

        # Check again that the node is in the db
        res = aiida.backends.sqlalchemy.session.query(DbNode.uuid).filter(
            DbNode.uuid == node_uuid).all()
        self.assertEqual(len(res), 1,
                         "There should be a node in the session/DB with the "
                         "UUID {}".format(node_uuid))
