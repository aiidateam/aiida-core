# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the migration engine (Alembic) as well as for the AiiDA migrations for SQLAlchemy."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from contextlib import contextmanager
import os

from alembic import command
from alembic.config import Config

from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy import manager
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.tests.test_utils import new_database
from aiida.backends.testbase import AiidaTestCase
from aiida.common.utils import Capturing


class TestMigrationsSQLA(AiidaTestCase):
    """
    This class contains tests for the migration mechanism of SQLAlchemy called
    alembic. It checks if the migrations can be applied and removed correctly.
    """
    # The path to the folder that contains the migration configuration (the
    # actual configuration - not the testing)
    migr_method_dir_path = None
    # The path of the migration configuration (the actual configuration - not
    # the testing)
    alembic_dpath = None

    migrate_from = None
    migrate_to = None

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Prepare the test class with the alembivc configuration
        """
        super(TestMigrationsSQLA, cls).setUpClass(*args, **kwargs)
        cls.manager = manager.SqlaBackendManager()

    def setUp(self):
        """
        Go to the migrate_from revision, apply setUpBeforeMigration, then
        run the migration.
        """
        super(TestMigrationsSQLA, self).setUp()
        from aiida.orm import autogroup

        self.current_autogroup = autogroup.current_autogroup
        autogroup.current_autogroup = None
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_to properties".format(type(self).__name__)

        try:
            with Capturing():
                self.migrate_db_down(self.migrate_from)
            self.setUpBeforeMigration()
            with Capturing():
                self.migrate_db_up(self.migrate_to)
        except Exception:
            # Bring back the DB to the correct state if this setup part fails
            self._reset_database_and_schema()
            raise

    def migrate_db_up(self, destination):
        """
        Perform a migration upwards (upgrade) with alembic

        :param destination: the name of the destination migration
        """
        # Undo all previous real migration of the database
        with self.manager.alembic_config() as config:
            command.upgrade(config, destination)

    def migrate_db_down(self, destination):
        """
        Perform a migration downwards (downgrade) with alembic

        :param destination: the name of the destination migration
        """
        with self.manager.alembic_config() as config:
            command.downgrade(config, destination)

    def tearDown(self):
        """
        Resets both the database content and the schema to prepare for the
        next test
        """
        from aiida.orm import autogroup
        self._reset_database_and_schema()
        autogroup.current_autogroup = self.current_autogroup
        super(TestMigrationsSQLA, self).tearDown()

    def setUpBeforeMigration(self):  # pylint: disable=invalid-name
        """
        Anything to do before running the migrations.
        This is typically implemented in test subclasses.
        """

    def _reset_database_and_schema(self):
        """
        Bring back the DB to the correct state.

        It is important to also reset the database content to avoid hanging
        of tests.
        """
        self.reset_database()
        with Capturing():
            self.migrate_db_up('head')

    @property
    def current_rev(self):
        """
        Utility method to get the current revision string
        """
        from alembic.migration import MigrationContext  # pylint: disable=import-error
        with sa.ENGINE.begin() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
        return current_rev

    @staticmethod
    def get_auto_base():
        """
        Return the automap_base class that automatically inspects the current
        database and return SQLAlchemy Models.

        Note that these are NOT the ones in AiiDA SQLAlchemy models, so do not
        have the special methods that we define there (like .save()).
        """
        from alembic.migration import MigrationContext  # pylint: disable=import-error
        from sqlalchemy.ext.automap import automap_base  # pylint: disable=import-error,no-name-in-module

        with sa.ENGINE.begin() as connection:
            context = MigrationContext.configure(connection)
            bind = context.bind

            base = automap_base()
            # reflect the tables
            base.prepare(bind.engine, reflect=True)

            return base

    @staticmethod
    @contextmanager
    def get_session():
        """
        Return a session that is properly closed after use.
        """
        from sqlalchemy.orm import Session  # pylint: disable=import-error,no-name-in-module

        with sa.ENGINE.begin() as connection:
            session = Session(connection.engine)
            yield session
            session.close()

    def get_current_table(self, table_name):
        """
        Return a Model instantiated at the correct migration.
        Note that this is obtained by inspecting the database and not
        by looking into the models file. So, special methods possibly defined
        in the models files/classes are not present.

        For instance, you can do::

          DbGroup = self.get_current_table('db_dbgroup')

        :param table_name: the name of the table.
        """
        base = self.get_auto_base()
        return getattr(base.classes, table_name)


class TestBackwardMigrationsSQLA(TestMigrationsSQLA):
    """
    This is the equivalent of TestMigrationsSQLA for backward migrations.
    It assumes that the migrate_from revision is higher in the hierarchy
    than the migrate_to revision.
    """

    def setUp(self):
        """
        Go to the migrate_from revision, apply setUpBeforeMigration, then
        run the migration.
        """
        AiidaTestCase.setUp(self)  # pylint: disable=bad-super-call
        from aiida.orm import autogroup

        self.current_autogroup = autogroup.current_autogroup
        autogroup.current_autogroup = None
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_to properties".format(type(self).__name__)

        try:
            with Capturing():
                self.migrate_db_down(self.migrate_from)
            self.setUpBeforeMigration()
            with Capturing():
                self.migrate_db_down(self.migrate_to)
        except Exception:
            # Bring back the DB to the correct state if this setup part fails
            self._reset_database_and_schema()
            raise


class TestMigrationSchemaVsModelsSchema(AiidaTestCase):
    """
    This class checks that the schema that results from a migration is the
    same generated by the models. This is important since migrations are
    frequently written by hand or extended manually and we have to ensure
    that the final result is what is conceived in the SQLA models.
    """
    # The path to the folder that contains the migration configuration (the
    # actual configuration - not the testing)
    migr_method_dir_path = None
    # The path of the migration configuration (the actual configuration - not
    # the testing)
    alembic_dpath = None
    # The alembic configuration needed for the migrations is stored here
    alembic_cfg_left = None

    # The URL of the databases
    db_url_left = None
    db_url_right = None

    def setUp(self):
        from sqlalchemydiff.util import get_temporary_uri
        from aiida.backends.sqlalchemy.migrations import versions

        self.migr_method_dir_path = os.path.dirname(os.path.realpath(manager.__file__))
        # Set the alembic script directory location
        self.alembic_dpath = os.path.join(self.migr_method_dir_path, manager.ALEMBIC_REL_PATH)  # pylint: disable=no-member

        # Constructing the versions directory
        versions_dpath = os.path.join(os.path.dirname(versions.__file__))

        # Setting dynamically the the path to the alembic configuration
        # (this is where the env.py file can be found)
        self.alembic_cfg_left = Config()
        self.alembic_cfg_left.set_main_option('script_location', self.alembic_dpath)
        # Setting dynamically the versions directory. These are the
        # migration scripts to pass from one version to the other. The
        # default ones are overridden with test-specific migrations.
        self.alembic_cfg_left.set_main_option('version_locations', versions_dpath)

        # The correction URL to the SQLA database of the current
        # AiiDA connection
        curr_db_url = sa.ENGINE.url

        # Create new urls for the two new databases
        self.db_url_left = get_temporary_uri(str(curr_db_url))
        self.db_url_right = get_temporary_uri(str(curr_db_url))

        # Put the correct database url to the database used by alembic
        self.alembic_cfg_left.set_main_option('sqlalchemy.url', self.db_url_left)

        # Database creation
        new_database(self.db_url_left)
        new_database(self.db_url_right)

    def tearDown(self):
        from sqlalchemydiff.util import destroy_database
        destroy_database(self.db_url_left)
        destroy_database(self.db_url_right)

    def test_model_and_migration_schemas_are_the_same(self):  # pylint: disable=invalid-name
        """Compare two databases.

        Compares the database obtained with all migrations against the
        one we get out of the models.  It produces a text file with the
        results to help debug differences.
        """
        from sqlalchemy.engine import create_engine  # pylint: disable=import-error,no-name-in-module
        from sqlalchemydiff import compare

        with create_engine(self.db_url_left).begin() as connection:
            self.alembic_cfg_left.attributes['connection'] = connection  # pylint: disable=unsupported-assignment-operation
            command.upgrade(self.alembic_cfg_left, 'head')

        engine_right = create_engine(self.db_url_right)
        Base.metadata.create_all(engine_right)
        engine_right.dispose()

        result = compare(self.db_url_left, self.db_url_right, set(['alembic_version']))
        self.assertTrue(
            result.is_match,
            'The migration database does not match to the one '
            'created by the models.\nDifferences: ' + result._dump_data(result.errors)  # pylint: disable=protected-access
        )
