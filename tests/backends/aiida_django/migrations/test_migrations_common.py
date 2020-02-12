# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module,invalid-name
""" The basic functionality for the migration tests"""
from django.apps import apps
from django.db.migrations.executor import MigrationExecutor
from django.db import connection

from aiida.backends.testbase import AiidaTestCase
from aiida.common.utils import Capturing


class TestMigrations(AiidaTestCase):
    """
    This is the common test class that is used by all migration tests. It migrates to a given
    migration point, allows you to set up the database & AiiDA at that point with the necessary
    data and migrates then to the final migration point.
    In the end it forwards the database at the final migration (as it should be and found before
    the migration tests).
    """

    @property
    def app(self):
        return apps.get_containing_app_config('aiida.backends.djsite.db').name.split('.')[-1]

    migrate_from = None
    migrate_to = None

    def setUp(self):
        """Go to a specific schema version before running tests."""
        from aiida.backends.djsite import get_scoped_session
        from aiida.orm import autogroup

        self.current_autogroup = autogroup.current_autogroup
        autogroup.current_autogroup = None
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_to properties".format(type(self).__name__)
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        self.apps = executor.loader.project_state(self.migrate_from).apps
        self.schema_editor = connection.schema_editor()

        # Before running the migration, make sure we close the querybuilder session which may still contain references
        # to objects whose mapping may be invalidated after resetting the schema to an older version. This can block
        # the migrations so we first expunge those objects by closing the session.
        get_scoped_session().close()

        # Reverse to the original migration
        with Capturing():
            executor.migrate(self.migrate_from)

        self.DbLink = self.apps.get_model('db', 'DbLink')
        self.DbNode = self.apps.get_model('db', 'DbNode')
        self.DbUser = self.apps.get_model('db', 'DbUser')
        self.DbUser.objects.all().delete()
        self.default_user = self.DbUser(1, 'aiida@localhost')
        self.default_user.save()

        try:
            self.setUpBeforeMigration()
            # Run the migration to test
            executor = MigrationExecutor(connection)
            executor.loader.build_graph()

            with Capturing():
                executor.migrate(self.migrate_to)

            self.apps = executor.loader.project_state(self.migrate_to).apps
        except Exception:
            # Bring back the DB to the correct state if this setup part fails
            import traceback
            traceback.print_stack()
            self._revert_database_schema()
            raise

    def tearDown(self):
        """At the end make sure we go back to the latest schema version."""
        from aiida.orm import autogroup
        self._revert_database_schema()
        autogroup.current_autogroup = self.current_autogroup

    def setUpBeforeMigration(self):
        """Anything to do before running the migrations, which should be implemented in test subclasses."""

    def _revert_database_schema(self):
        """Bring back the DB to the correct state."""
        from aiida.backends.djsite.db.migrations import LATEST_MIGRATION
        self.migrate_to = [(self.app, LATEST_MIGRATION)]
        executor = MigrationExecutor(connection)
        with Capturing():
            executor.migrate(self.migrate_to)

    def load_node(self, pk):
        return self.DbNode.objects.get(pk=pk)
