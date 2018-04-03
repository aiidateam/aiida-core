# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import copy
import unittest

import os
from alembic import command
from alembic.config import Config

from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy import utils
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.utils import (get_migration_head,
                                             get_db_schema_version)
from aiida.backends.testbase import AiidaTestCase
from aiida.common.setup import set_property, get_property

from aiida.backends.sqlalchemy.tests.utils import new_database


alembic_root = os.path.join(os.path.dirname(__file__), 'migrations', 'alembic')


TEST_ALEMBIC_REL_PATH = 'migration_test'


class TestMigrationApplicationSQLA(AiidaTestCase):
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

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestMigrationApplicationSQLA, cls).setUpClass(*args, **kwargs)
        cls.migr_method_dir_path = os.path.dirname(
            os.path.realpath(utils.__file__))

    def setUp(self):
        self.migrate_db_with_non_testing_migrations("base")

    def tearDown(self):
        self.migrate_db_with_non_testing_migrations("head")

    def migrate_db_with_non_testing_migrations(self, destination):
        if destination not in ["head", "base"]:
            raise TypeError("Only head & base are accepted as destination "
                            "values.")
        # Set the alembic script directory location
        self.alembic_dpath = os.path.join(self.migr_method_dir_path,
                                     utils.ALEMBIC_REL_PATH)
        alembic_cfg = Config()
        alembic_cfg.set_main_option('script_location', self.alembic_dpath)

        # Undo all previous real migration of the database
        with sa.engine.begin() as connection:
            alembic_cfg.attributes['connection'] = connection
            if destination == "head":
                command.upgrade(alembic_cfg, "head")
            else:
                command.downgrade(alembic_cfg, "base")

    def test_migrations_forward_backward(self):
        """
        This is a very broad test that checks that the migration mechanism
        works. More specifically, it checks that::

            - Alembic database migrations to specific versions work (upgrade &
              downgrade)

            - The methods that are checking the database schema version and perform
              the migration procedure to the last version work correctly.

        """
        from aiida.backends.sqlalchemy.tests.migration_test import versions
        from aiida.backends.sqlalchemy.utils import check_schema_version

        try:
            # Constructing the versions directory
            versions_dpath = os.path.join(
                os.path.dirname(versions.__file__))

            # Setting dynamically the the path to the alembic configuration
            # (this is where the env.py file can be found)
            alembic_cfg = Config()
            alembic_cfg.set_main_option('script_location', self.alembic_dpath)
            # Setting dynamically the versions directory. These are the
            # migration scripts to pass from one version to the other. The
            # default ones are overridden with test-specific migrations.
            alembic_cfg.set_main_option('version_locations', versions_dpath)

            # Using the connection initialized by the tests
            with sa.engine.begin() as connection:
                alembic_cfg.attributes['connection'] = connection

                self.assertIsNone(get_db_schema_version(alembic_cfg),
                                  "The initial database version should be "
                                  "None (no version) since the test setUp "
                                  "method should undo all migrations")
            # Migrate the database to the latest version
            check_schema_version(force_migration=True, alembic_cfg=alembic_cfg)
            with sa.engine.begin() as connection:
                alembic_cfg.attributes['connection'] = connection
                self.assertEquals(get_db_schema_version(alembic_cfg),
                                  get_migration_head(alembic_cfg),
                                  "The latest database version is not the "
                                  "expected one.")
            with sa.engine.begin() as connection:
                alembic_cfg.attributes['connection'] = connection
                # Migrating the database to the base version
                command.downgrade(alembic_cfg, "base")
                self.assertIsNone(get_db_schema_version(alembic_cfg),
                                  "The database version is not the expected "
                                  "one. It should be None (initial).")

        except Exception as test_ex:
            # If there is an exception, clean the alembic related tables
            from sqlalchemy.engine import reflection

            # Getting the current database table names
            inspector = reflection.Inspector.from_engine(
                sa.get_scoped_session().bind)
            db_table_names = set(inspector.get_table_names())
            # The alembic related database names
            alemb_table_names = set(['account', 'alembic_version'])

            # Get the intersection of the above tables
            tables_to_drop = set.intersection(db_table_names,
                                              alemb_table_names)
            # Delete only the tables that exist
            for table in tables_to_drop:
                from psycopg2 import ProgrammingError
                from sqlalchemy.orm import sessionmaker, scoped_session
                try:
                    with sa.engine.begin() as connection:
                        connection.execute('DROP TABLE {};'.format(table))
                except Exception as db_ex:
                    print("The following error occured during the cleaning of"
                          "the database: {}".format(db_ex.message))
            # Since the database cleaning is over, raise the test
            # exception that was caught
            raise test_ex


class TestMigrationSchemaVsModelsSchema(unittest.TestCase):
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
        # from aiida.backends.sqlalchemy.tests.migration_test import versions
        from sqlalchemydiff.util import get_temporary_uri
        from aiida.backends.sqlalchemy.migrations import versions

        self.migr_method_dir_path = os.path.dirname(
            os.path.realpath(utils.__file__))
        # Set the alembic script directory location
        self.alembic_dpath = os.path.join(self.migr_method_dir_path,
                                     utils.ALEMBIC_REL_PATH)

        # Constructing the versions directory
        versions_dpath = os.path.join(
            os.path.dirname(versions.__file__))

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
        curr_db_url = sa.engine.url

        # Create new urls for the two new databases
        self.db_url_left = get_temporary_uri(str(curr_db_url))
        self.db_url_right = get_temporary_uri(str(curr_db_url))

        # Put the correct database url to the database used by alembic
        self.alembic_cfg_left.set_main_option("sqlalchemy.url",
                                              self.db_url_left)

        # Database creation
        new_database(self.db_url_left)
        new_database(self.db_url_right)

    def tearDown(self):
        from sqlalchemydiff.util import destroy_database
        destroy_database(self.db_url_left)
        destroy_database(self.db_url_right)

    def test_model_and_migration_schemas_are_the_same(self):
        """Compare two databases.

        Compares the database obtained with all migrations against the
        one we get out of the models.  It produces a text file with the
        results to help debug differences.
        """
        from sqlalchemy.engine import create_engine
        from sqlalchemydiff import compare

        with create_engine(self.db_url_left).begin() as connection:
            self.alembic_cfg_left.attributes['connection'] = connection
            command.upgrade(self.alembic_cfg_left, "head")

        engine_right = create_engine(self.db_url_right)
        Base.metadata.create_all(engine_right)
        engine_right.dispose()

        result = compare(
            self.db_url_left, self.db_url_right, set(['alembic_version']))

        self.assertTrue(result.is_match,
                        "The migration database doesn't match to the one "
                        "created by the models.\nDifferences: " +
                        result._dump_data(result.errors))
