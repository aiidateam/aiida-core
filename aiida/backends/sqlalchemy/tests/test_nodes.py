# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Tests for nodes, attributes and links
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.orm import Data
from aiida import orm


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
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()

        from pytz import UTC
        from aiida.common import timezone
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
        from aiida.backends.sqlalchemy import get_scoped_session

        a = Data()
        a.store()

        self.assertEquals(a.pk, load_node(identifier=a.pk).pk)
        self.assertEquals(a.pk, load_node(identifier=a.uuid).pk)
        self.assertEquals(a.pk, load_node(pk=a.pk).pk)
        self.assertEquals(a.pk, load_node(uuid=a.uuid).pk)

        session = get_scoped_session()

        try:
            session.begin_nested()
            with self.assertRaises(ValueError):
                load_node(identifier=a.pk, pk=a.pk)
        finally:
            session.rollback()

        try:
            session.begin_nested()
            with self.assertRaises(ValueError):
                load_node(pk=a.pk, uuid=a.uuid)
        finally:
            session.rollback()

        try:
            session.begin_nested()
            with self.assertRaises(TypeError):
                load_node(pk=a.uuid)
        finally:
            session.rollback()

        try:
            session.begin_nested()
            with self.assertRaises(TypeError):
                load_node(uuid=a.pk)
        finally:
            session.rollback()

        try:
            session.begin_nested()
            with self.assertRaises(ValueError):
                load_node()
        finally:
            session.rollback()

    def test_multiple_node_creation(self):
        """
        This test checks that a node is not added automatically to the session
        (and subsequently committed) when a user is in the session.
        It tests the fix for the issue #234
        """
        from aiida.backends.sqlalchemy.models.node import DbNode
        from aiida.common.utils import get_new_uuid
        import aiida.backends.sqlalchemy

        backend = self.backend

        # Get the automatic user
        dbuser = backend.users.create("{}@aiida.net".format(self.id())).store().dbmodel
        # Create a new node but don't add it to the session
        node_uuid = get_new_uuid()
        DbNode(user=dbuser, uuid=node_uuid, node_type=None)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        # Query the session before commit
        res = session.query(DbNode.uuid).filter(
            DbNode.uuid == node_uuid).all()
        self.assertEqual(len(res), 0, "There should not be any nodes with this"
                                      "UUID in the session/DB.")

        # Commit the transaction
        session.commit()

        # Check again that the node is not in the DB
        res = session.query(DbNode.uuid).filter(
            DbNode.uuid == node_uuid).all()
        self.assertEqual(len(res), 0, "There should not be any nodes with this"
                                      "UUID in the session/DB.")

        # Get the automatic user
        dbuser = orm.User.objects.get_default().backend_entity.dbmodel
        # Create a new node but now add it to the session
        node_uuid = get_new_uuid()
        node = DbNode(user=dbuser, uuid=node_uuid, node_type=None)
        session.add(node)

        # Query the session before commit
        res = session.query(DbNode.uuid).filter(
            DbNode.uuid == node_uuid).all()
        self.assertEqual(len(res), 1,
                         "There should be a node in the session/DB with the "
                         "UUID {}".format(node_uuid))

        # Commit the transaction
        session.commit()

        # Check again that the node is in the db
        res = session.query(DbNode.uuid).filter(
            DbNode.uuid == node_uuid).all()
        self.assertEqual(len(res), 1,
                         "There should be a node in the session/DB with the "
                         "UUID {}".format(node_uuid))
