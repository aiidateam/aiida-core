# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module
""" This module contains the codebase for the setUpClass and tearDown methods used
internally by the AiidaTestCase. This inherits only from 'object' to avoid
that it is picked up by the automatic discovery of tests
(It shouldn't, as it risks to destroy the DB if there are not the checks
in place, and these are implemented in the AiidaTestCase. """

from aiida.backends.testimplbase import AiidaTestImplementation


class SqlAlchemyTests(AiidaTestImplementation):
    """Base class to test SQLA-related functionalities."""
    connection = None
    _backend = None

    def setUpClass_method(self):
        self.clean_db()

    def tearDownClass_method(self):
        """Backend-specific tasks for tearing down the test environment."""

    @property
    def backend(self):
        """Get the backend."""
        if self._backend is None:
            from aiida.manage.manager import get_manager
            self._backend = get_manager().get_backend()

        return self._backend

    def clean_db(self):
        from sqlalchemy.sql import table
        # pylint: disable=invalid-name
        DbGroupNodes = table('db_dbgroup_dbnodes')
        DbGroup = table('db_dbgroup')
        DbLink = table('db_dblink')
        DbNode = table('db_dbnode')
        DbLog = table('db_dblog')
        DbAuthInfo = table('db_dbauthinfo')
        DbUser = table('db_dbuser')
        DbComputer = table('db_dbcomputer')

        with self.backend.transaction() as session:
            session.execute(DbGroupNodes.delete())
            session.execute(DbGroup.delete())
            session.execute(DbLog.delete())
            session.execute(DbLink.delete())
            session.execute(DbNode.delete())
            session.execute(DbAuthInfo.delete())
            session.execute(DbComputer.delete())
            session.execute(DbUser.delete())
            session.commit()
