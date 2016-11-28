# -*- coding: utf-8 -*-

import unittest
import functools
import shutil
import os


from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


import aiida.backends.sqlalchemy
from aiida.common.utils import get_configured_user_email
from aiida.backends.sqlalchemy.utils import (install_tc, loads_json,
                                             dumps_json)
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.orm.computer import Computer

from aiida.common.setup import get_profile_config

from aiida.backends.settings import AIIDADB_PROFILE

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"

# Session = sessionmaker(expire_on_commit=False)
Session = sessionmaker(expire_on_commit=True)


class SqlAlchemyTests(unittest.TestCase):

    # Specify the need to drop the table at the beginning of a test case
    drop_all = False

    test_session = None

    @classmethod
    def setUpClass(cls, initial_data=True):

        if cls.test_session is None:
            config = get_profile_config(AIIDADB_PROFILE)
            engine_url = ("postgresql://{AIIDADB_USER}:{AIIDADB_PASS}@"
                          "{AIIDADB_HOST}:{AIIDADB_PORT}/{AIIDADB_NAME}").format(**config)
            engine = create_engine(engine_url,
                                   json_serializer=dumps_json,
                                   json_deserializer=loads_json)

            cls.connection = engine.connect()

            cls.test_session = Session(bind=cls.connection)
            aiida.backends.sqlalchemy.session = cls.test_session

        if cls.drop_all:
            Base.metadata.drop_all(cls.connection)
            Base.metadata.create_all(cls.connection)
            install_tc(cls.connection)
        else:
            cls.clean_db()

        if initial_data:
            email = get_configured_user_email()

            has_user = DbUser.query.filter(DbUser.email==email).first()
            if not has_user:
                cls.user = DbUser(get_configured_user_email(), "foo", "bar", "tests")
                cls.test_session.add(cls.user)
                cls.test_session.commit()

            has_computer = DbComputer.query.filter(DbComputer.hostname == 'localhost').first()
            if not has_computer:
                cls.computer = SqlAlchemyTests._create_computer()
                cls.computer.store()


    @staticmethod
    def _create_computer(**kwargs):
        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro',
                        workdir='/tmp/aiida')
        defaults.update(kwargs)
        return Computer(**defaults)

    @staticmethod
    def inject_computer(f):
        @functools.wraps(f)
        def dec(*args, **kwargs):
            computer = DbComputer.query.filter_by(name="localhost").first()
            args = list(args)
            args.insert(1, computer)
            return f(*args, **kwargs)

        return dec

    @classmethod
    def clean_db(cls):
        from aiida.backends.sqlalchemy.models.computer import DbComputer
        from aiida.backends.sqlalchemy.models.workflow import DbWorkflow
        from aiida.backends.sqlalchemy.models.group import DbGroup
        from aiida.backends.sqlalchemy.models.node import DbLink
        from aiida.backends.sqlalchemy.models.node import DbNode
        from aiida.backends.sqlalchemy.models.log import DbLog
        from aiida.backends.sqlalchemy.models.user import DbUser

        # Delete the workflows
        cls.test_session.query(DbWorkflow).delete()

        # Empty the relationship dbgroup.dbnode
        dbgroups = cls.test_session.query(DbGroup).all()
        for dbgroup in dbgroups:
            dbgroup.dbnodes = []

        # Delete the groups
        cls.test_session.query(DbGroup).delete()

        # I first need to delete the links, because in principle I could
        # not delete input nodes, only outputs. For simplicity, since
        # I am deleting everything, I delete the links first
        cls.test_session.query(DbLink).delete()

        # Then I delete the nodes, otherwise I cannot
        # delete computers and users
        cls.test_session.query(DbNode).delete()

        # # Delete the users
        # cls.test_session.query(DbUser).delete()

        # Delete the computers
        cls.test_session.query(DbComputer).delete()

        # Delete the logs
        cls.test_session.query(DbLog).delete()

        cls.test_session.commit()

    @classmethod
    def tearDownClass(cls):
        from aiida.settings import REPOSITORY_PATH
        from aiida.common.setup import TEST_KEYWORD
        from aiida.common.exceptions import InvalidOperation
        if TEST_KEYWORD not in REPOSITORY_PATH:
            raise InvalidOperation("Be careful. The repository for the tests "
                                   "is not a test repository. I will not "
                                   "empty the database and I will not delete "
                                   "the repository. Repository path: "
                                   "{}".format(REPOSITORY_PATH))

        cls.clean_db()

        cls.test_session.close()
        cls.test_session = None

        cls.connection.close()


        # I clean the test repository
        shutil.rmtree(REPOSITORY_PATH, ignore_errors=True)
        os.makedirs(REPOSITORY_PATH)
