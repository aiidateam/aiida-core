# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import functools
import os
import shutil

from sqlalchemy.orm import sessionmaker

import aiida.backends.sqlalchemy
from aiida.backends.settings import AIIDADB_PROFILE
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.backends.sqlalchemy.utils import install_tc
from aiida.backends.testimplbase import AiidaTestImplementation
from aiida.common.setup import get_profile_config
from aiida.common.utils import get_configured_user_email
from aiida.orm.computer import Computer


# Querying for expired objects automatically doesn't seem to work.
# That's why expire on commit=False resolves many issues of objects beeing
# obsolete

expire_on_commit = True
Session = sessionmaker(expire_on_commit=expire_on_commit)

# This contains the codebase for the setUpClass and tearDown methods used internally by the AiidaTestCase
# This inherits only from 'object' to avoid that it is picked up by the automatic discovery of tests
# (It shouldn't, as it risks to destroy the DB if there are not the checks in place, and these are
# implemented in the AiidaTestCase
class SqlAlchemyTests(AiidaTestImplementation):

    # Specify the need to drop the table at the beginning of a test case
    # If True, completely drops the tables and recreates the schema, 
    # but this is usually unnecessary and pretty slow
    # Also, if the tests are interrupted, there is the risk that the
    # DB remains dropped, so you have to do 'verdi -p test_xxx setup' again to
    # install the schema again
    drop_all = False

    test_session = None
    connection = None

    def setUpClass_method(self):

        from aiida.backends.sqlalchemy import get_scoped_session

        if self.test_session is None:
            # Should we use reset_session?
            self.test_session = get_scoped_session()

        if self.drop_all:
            Base.metadata.drop_all(self.test_session.connection)
            Base.metadata.create_all(self.test_session.connection)
            install_tc(self.test_session.connection)
        else:
            self.clean_db()

        self.insert_data()

    def setUp_method(self):
        pass

    def tearDown_method(self):
        pass

    def insert_data(self):
        """
        Insert default data into the DB.
        """
        email = get_configured_user_email()

        has_user = DbUser.query.filter(DbUser.email==email).first()
        if not has_user:
            self.user = DbUser(get_configured_user_email(), "foo", "bar",
                               "tests")
            self.test_session.add(self.user)
            self.test_session.commit()
        else:
            self.user = has_user

        # Required by the calling class
        self.user_email = self.user.email

        # Also self.computer is required by the calling class
        has_computer = DbComputer.query.filter(DbComputer.hostname ==
                                               'localhost').first()
        if not has_computer:
            self.computer = SqlAlchemyTests._create_computer()
            self.computer.store()
        else:
            self.computer = Computer(dbcomputer=has_computer)

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

    def clean_db(self):
        from aiida.backends.sqlalchemy.models.computer import DbComputer
        from aiida.backends.sqlalchemy.models.workflow import DbWorkflow, table_workflowstep_calc, \
            table_workflowstep_subworkflow, DbWorkflowStep, DbWorkflowData
        from aiida.backends.sqlalchemy.models.group import DbGroup
        from aiida.backends.sqlalchemy.models.node import DbLink
        from aiida.backends.sqlalchemy.models.node import DbNode
        from aiida.backends.sqlalchemy.models.log import DbLog
        from aiida.backends.sqlalchemy.models.user import DbUser

        # Delete the workflows
        # Complicated way to make sure we 'unwind' all the relationships
        # between workflows and their children.
        self.test_session.connection().execute(table_workflowstep_calc.delete())
        self.test_session.connection().execute(table_workflowstep_subworkflow.delete())
        self.test_session.query(DbWorkflowData).delete()
        self.test_session.query(DbWorkflowStep).delete()
        self.test_session.query(DbWorkflow).delete()

        # Empty the relationship dbgroup.dbnode
        dbgroups = self.test_session.query(DbGroup).all()
        for dbgroup in dbgroups:
            dbgroup.dbnodes = []

        # Delete the groups
        self.test_session.query(DbGroup).delete()

        # I first need to delete the links, because in principle I could
        # not delete input nodes, only outputs. For simplicity, since
        # I am deleting everything, I delete the links first
        self.test_session.query(DbLink).delete()

        # Then I delete the nodes, otherwise I cannot
        # delete computers and users
        self.test_session.query(DbNode).delete()

        # # Delete the users
        self.test_session.query(DbUser).delete()

        # Delete the computers
        self.test_session.query(DbComputer).delete()

        # Delete the logs
        self.test_session.query(DbLog).delete()

        self.test_session.commit()

    def tearDownClass_method(self):
        from aiida.settings import REPOSITORY_PATH
        from aiida.common.setup import TEST_KEYWORD
        from aiida.common.exceptions import InvalidOperation
        if TEST_KEYWORD not in REPOSITORY_PATH:
            raise InvalidOperation("Be careful. The repository for the tests "
                                   "is not a test repository. I will not "
                                   "empty the database and I will not delete "
                                   "the repository. Repository path: "
                                   "{}".format(REPOSITORY_PATH))

        self.clean_db()

        self.test_session.close()
        self.test_session = None

        # I clean the test repository
        shutil.rmtree(REPOSITORY_PATH, ignore_errors=True)
        os.makedirs(REPOSITORY_PATH)
