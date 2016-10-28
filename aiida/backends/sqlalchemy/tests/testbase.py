# -*- coding: utf-8 -*-

import unittest
import functools
import shutil
import os


from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


from aiida.backends import sqlalchemy as sa
from aiida.common.utils import get_configured_user_email
from aiida.backends.sqlalchemy.utils import (install_tc, loads_json,
                                             dumps_json)
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.orm.computer import Computer

from aiida.common.setup import get_profile_config

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"

Session = sessionmaker()


class SqlAlchemyTests(unittest.TestCase):

    # Specify the need to drop the table at the beginning of a test case
    drop_all = False

    @classmethod
    def setUpClass(cls):

        config = get_profile_config("sqla2")
        engine_url = ("postgresql://{AIIDADB_USER}:{AIIDADB_PASS}@"
                      "{AIIDADB_HOST}:{AIIDADB_PORT}/{AIIDADB_NAME}").format(**config)
        engine = create_engine(engine_url,
                               json_serializer=dumps_json,
                               json_deserializer=loads_json)

        cls.connection = engine.connect()

        session = Session(bind=cls.connection)
        sa.session = session

        if cls.drop_all:
            Base.metadata.drop_all(cls.connection)
        Base.metadata.create_all(cls.connection)
        install_tc(cls.connection)

        email = get_configured_user_email()

        has_user = DbUser.query.filter(DbUser.email==email).first()
        if not has_user:
            user = DbUser(email, "foo", "bar", "tests")
            sa.session.add(user)
            sa.session.commit()
            sa.session.expire_all()

        has_computer = DbComputer.query.filter(DbComputer.hostname == 'localhost').first()
        if not has_computer:
            computer = SqlAlchemyTests._create_computer()
            computer.store()

        session.close()

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


    # @classmethod
    # def tearDownClass(cls):
    #     # Clean what we added before
    #     cls.connection.close()
    #     config = get_profile_config("tests")
    #     repo_dir = config["AIIDADB_REPOSITORY_URI"]
    #     # We only treat the case where its a folder
    #     if repo_dir.startswith("file://"):
    #         repo_dir = repo_dir.split("file://")[-1]
    #         try:
    #             shutil.rmtree(repo_dir)
    #         except OSError:
    #             # If the folder doesn't exist, we don't care
    #             pass

    @classmethod
    def tearDownClass(cls):
        from aiida.settings import REPOSITORY_PATH
        from aiida.common.setup import TEST_REPO_PREFIX
        from aiida.common.exceptions import InvalidOperation
        if not os.path.basename(REPOSITORY_PATH).startswith(
                TEST_REPO_PREFIX):
            raise InvalidOperation("Be careful. The repository for the tests "
                                   "is not a test repository. I will not "
                                   "empty the database and I will not delete "
                                   "the repository. Repository path: "
                                   "{}".format(REPOSITORY_PATH))

        from aiida.backends.sqlalchemy.models.computer import DbComputer

        # I first delete the workflows
        from aiida.backends.sqlalchemy.models.workflow import DbWorkflow

        DbWorkflow.query.delete()

        # Delete groups
        # from aiida.backends.djsite.db.models import DbGroup
        from aiida.backends.sqlalchemy.models.group import DbGroup

        DbGroup.query.delete()
        # DbGroup.objects.all().delete()

        # I first need to delete the links, because in principle I could
        # not delete input nodes, only outputs. For simplicity, since
        # I am deleting everything, I delete the links first
        # from aiida.backends.djsite.db.models import DbLink
        from aiida.backends.sqlalchemy.models.node import DbLink

        DbLink.query.delete()
        # DbLink.objects.all().delete()

        # Then I delete the nodes, otherwise I cannot
        # delete computers and users
        # from aiida.backends.djsite.db.models import DbNode
        from aiida.backends.sqlalchemy.models.node import DbNode

        DbNode.query.delete()
        # DbNode.objects.all().delete()

        ## I do not delete it, see discussion in setUpClass
        # try:
        #    DbUser.objects.get(email=get_configured_user_email()).delete()
        # except ObjectDoesNotExist:
        #    pass

        # DbComputer.objects.all().delete()
        DbComputer.query.delete()

        # from aiida.backends.djsite.db.models import DbLog
        from aiida.backends.sqlalchemy.models.log import DbLog

        DbLog.query.delete()

        # I clean the test repository
        shutil.rmtree(REPOSITORY_PATH, ignore_errors=True)
        os.makedirs(REPOSITORY_PATH)

    def setUp(self):
        connec = self.__class__.connection
        self.trans = connec.begin()
        self.session = Session(bind=connec)
        sa.session = self.session

        dbcomputer = DbComputer.query.filter_by(name="localhost").first()
        self.computer = Computer(dbcomputer=dbcomputer)

        self.session.begin_nested()

        # then each time that SAVEPOINT ends, reopen it
        @event.listens_for(self.session, "after_transaction_end")
        def restart_savepoint(session, transaction):
            if transaction.nested and not transaction._parent.nested:

                # ensure that state is expired the way
                # session.commit() at the top level normally does
                # (optional step)
                session.expire_all()

                session.begin_nested()

    def tearDown(self):
        self.session.rollback()
        self.session.close()
        self.trans.rollback()
