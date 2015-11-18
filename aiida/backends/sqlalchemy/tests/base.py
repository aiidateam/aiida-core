# -*- coding: utf-8 -*-

import unittest


from sqlalchemy import create_engine



from aiida.backends import sqlalchemy
from aiida.backends.sqlalchemy.utils import (
    load_dbenv, is_dbenv_loaded, get_configured_user_email, get_automatic_user,
    install_tc
)
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.orm.computer import Computer

from aiida.common.setup import get_profile_config

class SqlAlchemyTests(unittest.TestCase):

    # Specify the need to drop the table at the beginning of a test case
    drop_all = False

    @classmethod
    def setUpClass(cls):
        if not is_dbenv_loaded():
            load_dbenv()

        cls._session = sqlalchemy.session
        cls._engine = cls._session.bind

        if cls.drop_all:
            Base.metadata.drop_all(cls._engine)
        Base.metadata.create_all(cls._engine)
        install_tc(cls._session)

        email = get_configured_user_email()

        user = DbUser.query.filter_by(email=email).first()
        if not user:
            user = DbUser(email, "foo", "bar", "tests")
            cls._session.add(user)

        cls.computer = DbComputer.query.filter_by(name="localhost").first()
        if not cls.computer:
            cls.computer = Computer(name='localhost',
                                    hostname='localhost',
                                    transport_type='local',
                                    scheduler_type='pbspro',
                                    workdir='/tmp/aiida')
            cls.computer.store()

        cls._user = user

    @classmethod
    def tearDownClass(cls):
        cls._session.close()

    def setUp(self):
        self.__class__._session.begin_nested()

    def tearDown(self):
        self.__class__._session.rollback()


