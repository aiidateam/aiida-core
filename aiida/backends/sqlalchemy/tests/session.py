# -*- coding: utf-8 -*-
"""
Tests Session possible problems
"""

import os
import shutil
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import aiida.backends.sqlalchemy
from aiida.backends.settings import AIIDADB_PROFILE
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.utils import (install_tc, loads_json,
                                             dumps_json)
from aiida.common.setup import get_profile_config
from aiida.settings import REPOSITORY_PATH
from aiida.common.utils import get_configured_user_email
from aiida.backends.testbase import AiidaTestCase

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestSessionSqla(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def set_connection(self, expire_on_commit=True):

        config = get_profile_config(AIIDADB_PROFILE)
        engine_url = ("postgresql://{AIIDADB_USER}:{AIIDADB_PASS}@"
                      "{AIIDADB_HOST}:{AIIDADB_PORT}/{AIIDADB_NAME}").format(
            **config)
        engine = create_engine(engine_url,
                               json_serializer=dumps_json,
                               json_deserializer=loads_json)

        Session = sessionmaker(expire_on_commit=expire_on_commit)

        # Session = sessionmaker(expire_on_commit=expire_on_commit)
        self.connection = engine.connect()
        aiida.backends.sqlalchemy.session = Session(bind=self.connection)

        # Clean the test repository
        shutil.rmtree(REPOSITORY_PATH, ignore_errors=True)
        os.makedirs(REPOSITORY_PATH)

        # Clean the database (drop it & create it properly)
        try:
            aiida.backends.sqlalchemy.session.begin_nested()
            Base.metadata.drop_all(self.connection, checkfirst=False)
            # Base.metadata.drop_all(self.connection)
        except Exception as e:
            print e
            aiida.backends.sqlalchemy.session.rollback()

        Base.metadata.create_all(self.connection)
        install_tc(self.connection)

        Base.metadata.reflect(engine)
        aiida.backends.sqlalchemy.session.expunge_all()

    def drop_connection(self):
        # Clean-up
        aiida.backends.sqlalchemy.session.expunge_all()
        aiida.backends.sqlalchemy.session.close()
        aiida.backends.sqlalchemy.session = None
        self.connection.close()

    @unittest.skip("")
    def test_session_update_and_expiration_1(self):

        self.set_connection(expire_on_commit=True)

        from aiida.orm.computer import Computer
        from aiida.orm.code import Code
        from aiida.orm.user import User

        user = User(email=get_configured_user_email())
        aiida.backends.sqlalchemy.session.add(user._dbuser)
        aiida.backends.sqlalchemy.session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro',
                        workdir='/tmp/aiida')
        computer = Computer(**defaults)
        aiida.backends.sqlalchemy.session.add(computer._dbcomputer)
        aiida.backends.sqlalchemy.session.commit()

        print aiida.backends.sqlalchemy.session.hash_key

        code = Code()
        code.set_remote_computer_exec((computer, '/x.x'))
        aiida.backends.sqlalchemy.session.add(code.dbnode)
        aiida.backends.sqlalchemy.session.commit()

        self.drop_connection()

    @unittest.skip("")
    def test_session_update_and_expiration_2(self):
        from aiida.backends.sqlalchemy.models.user import DbUser
        from aiida.backends.sqlalchemy.models.computer import DbComputer

        self.set_connection(expire_on_commit=True)

        from aiida.orm.computer import Computer
        from aiida.orm.code import Code
        from aiida.orm.user import User

        user = User(email=get_configured_user_email())
        aiida.backends.sqlalchemy.session.add(user._dbuser)
        aiida.backends.sqlalchemy.session.commit()

        # aiida.backends.sqlalchemy.session.expunge_all()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro',
                        workdir='/tmp/aiida')
        computer = Computer(**defaults)
        computer.store()
        # aiida.backends.sqlalchemy.session.expunge_all()
        # aiida.backends.sqlalchemy.session.add(computer._dbcomputer)
        # aiida.backends.sqlalchemy.session.commit()

        aiida.backends.sqlalchemy.session.refresh(computer._dbcomputer)

        # aiida.backends.sqlalchemy.session.expunge(user._dbuser)
        # aiida.backends.sqlalchemy.session.refresh(user._dbuser)
        # import time
        # time.sleep(2)

        print aiida.backends.sqlalchemy.session.hash_key
        code = Code()
        code.set_remote_computer_exec((computer, '/x.x'))
        code.store()
        # aiida.backends.sqlalchemy.session.add(code.dbnode)
        # aiida.backends.sqlalchemy.session.commit()


        self.drop_connection()

    @unittest.skip("")
    def test_session_update_and_expiration_3(self):

        self.set_connection(expire_on_commit=False)

        from aiida.orm.computer import Computer
        from aiida.orm.code import Code
        from aiida.orm.user import User

        user = User(email=get_configured_user_email())
        aiida.backends.sqlalchemy.session.add(user._dbuser)
        aiida.backends.sqlalchemy.session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro',
                        workdir='/tmp/aiida')
        computer = Computer(**defaults)
        aiida.backends.sqlalchemy.session.add(computer._dbcomputer)
        aiida.backends.sqlalchemy.session.commit()

        print aiida.backends.sqlalchemy.session.hash_key

        code = Code()
        code.set_remote_computer_exec((computer, '/x.x'))
        aiida.backends.sqlalchemy.session.add(code.dbnode)
        aiida.backends.sqlalchemy.session.commit()

        self.drop_connection()

    @unittest.skip("")
    def test_session_update_and_expiration_4(self):

        self.set_connection(expire_on_commit=False)

        from aiida.orm.computer import Computer
        from aiida.orm.code import Code
        from aiida.orm.user import User

        user = User(email=get_configured_user_email())
        aiida.backends.sqlalchemy.session.add(user._dbuser)
        aiida.backends.sqlalchemy.session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro',
                        workdir='/tmp/aiida')
        computer = Computer(**defaults)
        computer.store()

        print aiida.backends.sqlalchemy.session.hash_key
        # aiida.backends.sqlalchemy.session.refresh(computer._dbcomputer)

        code = Code()
        code.set_remote_computer_exec((computer, '/x.x'))
        code.store()

        self.drop_connection()

    @unittest.skip("")
    def test_multiple_node_creation(self):
        from aiida.backends.sqlalchemy.models.node import DbNode
        from aiida.common.utils import get_new_uuid
        from aiida.backends.utils import get_automatic_user
        from aiida.orm.user import User

        import aiida.backends.sqlalchemy

        # Initialize the database
        self.set_connection(expire_on_commit=False)

        # Create a new user
        user = User(email=get_configured_user_email())
        aiida.backends.sqlalchemy.session.add(user._dbuser)
        aiida.backends.sqlalchemy.session.commit()

        # Retrieve a fresh user since the session expires
        user = get_automatic_user()
        # Create a new user but don't add it to the session
        user_uuid = get_new_uuid()
        DbNode(user=user, uuid=user_uuid, type=None)

        # Query the session before commit
        res = aiida.backends.sqlalchemy.session.query(DbNode.uuid).filter(
            DbNode.uuid == user_uuid).all()
        self.assertEqual(len(res), 0, "There should not be any nodes with this"
                                      "UUID in the session/DB.")

        # Commit the transaction
        aiida.backends.sqlalchemy.session.commit()

        # Check again that there isn't anything in the DB
        res = aiida.backends.sqlalchemy.session.query(DbNode.uuid).filter(
            DbNode.uuid == user_uuid).all()
        self.assertEqual(len(res), 0, "There should not be any nodes with this"
                                      "UUID in the session/DB.")

        # Retrieve a fresh user since the session expires
        user = get_automatic_user()
        # Create a new user but now add it to the session
        user_uuid = get_new_uuid()
        node = DbNode(user=user, uuid=user_uuid, type=None)
        aiida.backends.sqlalchemy.session.add(node)

        # Query the session before commit
        res = aiida.backends.sqlalchemy.session.query(DbNode.uuid).filter(
            DbNode.uuid == user_uuid).all()
        self.assertEqual(len(res), 1,
                         "There should be a node in the session/DB with the "
                         "UUID {}".format(user_uuid))

        # Commit the transaction
        aiida.backends.sqlalchemy.session.commit()

        # Check again that there isn't anything in the DB
        res = aiida.backends.sqlalchemy.session.query(DbNode.uuid).filter(
            DbNode.uuid == user_uuid).all()
        self.assertEqual(len(res), 1,
                         "There should be a node in the session/DB with the "
                         "UUID {}".format(user_uuid))

        self.drop_connection()

    @unittest.skip("")
    def test_multiple_node_creation_gio(self):
        from aiida.orm.user import User
        from aiida.backends.sqlalchemy.models.node import DbNode
        from aiida.common.utils import get_new_uuid

        config = get_profile_config(AIIDADB_PROFILE)
        engine_url = ("postgresql://{AIIDADB_USER}:{AIIDADB_PASS}@"
                      "{AIIDADB_HOST}:{AIIDADB_PORT}/{AIIDADB_NAME}").format(
            **config)
        engine = create_engine(engine_url,
                               json_serializer=dumps_json,
                               json_deserializer=loads_json)

        self.connection = engine.connect()
        Session = sessionmaker(expire_on_commit=True)


        s0 = Session(bind=self.connection)
        # Clean the database (drop it & create it properly)
        try:
            s0.begin_nested()
            Base.metadata.drop_all(self.connection, checkfirst=False)
            # Base.metadata.drop_all(self.connection)
        except Exception as e:
            print e
            s0.rollback()

        Base.metadata.create_all(self.connection)
        install_tc(self.connection)

        Base.metadata.reflect(engine)

        # Session = sessionmaker(expire_on_commit=expire_on_commit)

        s1 = Session(bind=self.connection)

        dbuser = User(email="a@bbb.cc")._dbuser
        s1.add(dbuser)

        dbn1 = DbNode(user=dbuser, uuid=get_new_uuid(), type=None)
        s1.add(dbn1)

        s1.commit()

        s1.expunge(dbuser)

        s2 = Session(bind=self.connection)
        dbn2 = DbNode(user=dbuser, uuid=get_new_uuid(), type=None)
        s2.add(dbn2)

        s2.commit()




















