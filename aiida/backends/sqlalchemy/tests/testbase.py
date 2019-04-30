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

from aiida.backends.testimplbase import AiidaTestImplementation
from aiida.orm.implementation.sqlalchemy.backend import SqlaBackend


# This contains the codebase for the setUpClass and tearDown methods used
# internally by the AiidaTestCase. This inherits only from 'object' to avoid
# that it is picked up by the automatic discovery of tests
# (It shouldn't, as it risks to destroy the DB if there are not the checks
# in place, and these are implemented in the AiidaTestCase
class SqlAlchemyTests(AiidaTestImplementation):

    connection = None
    test_session = None

    def setUpClass_method(self):
        from aiida.backends.sqlalchemy import get_scoped_session

        if self.test_session is None:
            # Should we use reset_session?
            self.test_session = get_scoped_session()

        self.clean_db()
        self.backend = SqlaBackend()

    def setUp_method(self):
        pass

    def tearDown_method(self):
        pass

    def clean_db(self):
        from sqlalchemy.sql import table

        DbGroupNodes = table('db_dbgroup_dbnodes')
        DbGroup = table('db_dbgroup')
        DbLink = table('db_dblink')
        DbNode = table('db_dbnode')
        DbLog = table('db_dblog')
        DbAuthInfo = table('db_dbauthinfo')
        DbUser = table('db_dbuser')
        DbComputer = table('db_dbcomputer')

        self.test_session.execute(DbGroupNodes.delete())
        self.test_session.execute(DbGroup.delete())
        self.test_session.execute(DbLog.delete())
        self.test_session.execute(DbLink.delete())
        self.test_session.execute(DbNode.delete())
        self.test_session.execute(DbAuthInfo.delete())
        self.test_session.execute(DbComputer.delete())
        self.test_session.execute(DbUser.delete())

        self.test_session.commit()

    def tearDownClass_method(self):
        """
        Backend-specific tasks for tearing down the test environment.
        """
        self.test_session.close()
        self.test_session = None
