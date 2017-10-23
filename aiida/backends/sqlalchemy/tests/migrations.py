# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import os
import logging
import copy

from alembic import command
from alembic.config import Config

from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy import utils
from aiida.backends.sqlalchemy.utils import (get_migration_head,
                                             get_db_schema_version)
from aiida.backends.testbase import AiidaTestCase
from aiida.common.setup import set_property, get_property

TEST_ALEMBIC_REL_PATH = 'migration_test'


from unittest import skip


class TestMigrationsSQLA(AiidaTestCase):
    """
    This class contains tests for the migration mechanism of SQLAlchemy called
    alembic.
    """
    # The path to the folder that contains the migration configuration (the
    # actual configuration - not the testing)
    migr_method_dir_path = None
    # The path of the migration configuration (the actual configuration - not
    # the testing)
    alembic_dpath = None
    # The initial alembic log level - to be restored after the testing
    init_alemb_log_level = ''

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestMigrationsSQLA, cls).setUpClass(*args, **kwargs)
        cls.migr_method_dir_path = os.path.dirname(
            os.path.realpath(utils.__file__))

    def setUp(self):
        self.init_alemb_log_level = get_property('logging.alembic_loglevel')
        set_property('logging.alembic_loglevel',
                     logging.getLevelName(logging.ERROR))
        self.migrate_db_with_non_testing_migrations("base")

    def tearDown(self):
        self.migrate_db_with_non_testing_migrations("head")
        set_property('logging.alembic_loglevel',
                     logging.getLevelName(self.init_alemb_log_level))

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

    @skip("")
    def test_migrations_forward_backward(self):
        """
        This is a very broad test that checks that the migration mechanism
        works. More specifically, it checks that:
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


import os
import unittest


from sqlalchemy_utils.functions.database import drop_database
from alembic import command
from sqlalchemydiff import compare
from sqlalchemydiff.util import (
    destroy_database,
    get_temporary_uri,
    new_db,
    prepare_schema_from_models,
)

from alembicverify.util import (
    get_current_revision,
    get_head_revision,
    make_alembic_config,
    prepare_schema_from_migrations,
)
# from .models import Base
from aiida.backends.sqlalchemy.models.base import Base

alembic_root = os.path.join(os.path.dirname(__file__), 'migrations', 'alembic')


class TestExample(unittest.TestCase):
    # The path to the folder that contains the migration configuration (the
    # actual configuration - not the testing)
    migr_method_dir_path = None
    # The path of the migration configuration (the actual configuration - not
    # the testing)
    alembic_dpath = None
    # The initial alembic log level - to be restored after the testing
    init_alemb_log_level = ''


    def setUp(self):
        # from aiida.backends.sqlalchemy import engine
        # engine.dispose()

        # uri = (
        #     "mysql+mysqlconnector://root:password@localhost:3306/alembicverify"
        # )
        #
        # self.uri_left = get_temporary_uri(uri)
        # self.uri_right = get_temporary_uri(uri)
        #
        # self.alembic_config_left = make_alembic_config(
        #     self.uri_left, alembic_root)
        # self.alembic_config_right = make_alembic_config(
        #     self.uri_right, alembic_root)
        #
        # new_db(self.uri_left)
        # new_db(self.uri_right)

        # from aiida.backends.sqlalchemy.tests.migration_test import versions
        from aiida.backends.sqlalchemy.migrations import versions
        from aiida.backends.sqlalchemy.utils import check_schema_version

        self.migr_method_dir_path = os.path.dirname(
            os.path.realpath(utils.__file__))
        # Set the alembic script directory location
        self.alembic_dpath = os.path.join(self.migr_method_dir_path,
                                     utils.ALEMBIC_REL_PATH)

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

            # The correction URL to the SQLA database of the current
            # AiiDA connection
            curr_db_url = sa.engine.url

            # Create new urls for the two new databases
            self.db_url_left = get_temporary_uri(str(curr_db_url))
            # self.db_url_left = self.db_url_left.replace('postgresql', 'postgresql+psycopg2')
            self.db_url_right = get_temporary_uri(str(curr_db_url))
            # self.db_url_right = self.db_url_right.replace('postgresql',
            #                                             'postgresql+psycopg2')

            # Create new alembic configurations for the two new databases
            self.alembic_cfg_left = copy.copy(alembic_cfg)
            self.alembic_cfg_right = copy.copy(alembic_cfg)

            # Put the correct database urls to the databases
            self.alembic_cfg_left.set_main_option("sqlalchemy.url",
                                                  self.db_url_left)
            self.alembic_cfg_right.set_main_option("sqlalchemy.url",
                                                   self.db_url_right)

            # Database creation
            print 'self.db_url_left ', self.db_url_left
            new_database(self.db_url_left)

            import time
            time.sleep(10)
            print 'self.db_url_right ', self.db_url_right
            new_database(self.db_url_right)

        except Exception as ex:
            print ex.message
            import traceback
            traceback.print_exc()
            raise ex


        # uri = (
        #     "mysql+mysqlconnector://root:password@localhost:3306/alembicverify"
        # )
        #
        # self.uri_left = get_temporary_uri(uri)
        # self.uri_right = get_temporary_uri(uri)
        #
        # self.alembic_config_left = make_alembic_config(
        #     self.uri_left, alembic_root)
        # self.alembic_config_right = make_alembic_config(
        #     self.uri_right, alembic_root)
        #
        # new_db(self.uri_left)
        # new_db(self.uri_right)


    def tearDown(self):
        destroy_database(self.db_url_left)
        destroy_database(self.db_url_right)

    @skip("")
    def test_upgrade_and_downgrade(self):
        """Test all migrations up and down.

        Tests that we can apply all migrations from a brand new empty
        database, and also that we can remove them all.
        """
        engine, script = prepare_schema_from_migrations(
            self.uri_left, self.alembic_config_left)

        head = get_head_revision(self.alembic_config_left, engine, script)
        current = get_current_revision(
            self.alembic_config_left, engine, script)

        assert head == current

        while current is not None:
            command.downgrade(self.alembic_config_left, '-1')
            current = get_current_revision(
                self.alembic_config_left, engine, script)

    def test_model_and_migration_schemas_are_the_same(self):
        """Compare two databases.

        Compares the database obtained with all migrations against the
        one we get out of the models.  It produces a text file with the
        results to help debug differences.
        """
        le = self.create_engine(self.db_url_left)
        conn = le.connect()

        with self.create_engine(self.db_url_left).begin() as connection:
            self.alembic_cfg_left.attributes['connection'] = connection
            command.upgrade(self.alembic_cfg_left, "head")

        # prepare_schema_from_migrations(self.db_url_left, self.alembic_cfg_left)
        # prepare_schema_from_models(self.db_url_right, Base)

        engine_right = self.create_engine(self.db_url_right)
        Base.metadata.create_all(engine_right)
        # with self.create_engine(self.db_url_right) as engine_right:
        #     Base.metadata.create_all(engine_right)
        engine_right.dispose()

        result = compare(
            self.db_url_left, self.db_url_right, set(['alembic_version']))

        self.assertTrue(result.is_match, "The migration database doesn't"
                                         "match to the one created by the"
                                         "models.")

        assert result.is_match

    def create_engine(self, engine_url):
        from sqlalchemy.engine import create_engine
        from aiida.backends.sqlalchemy.utils import (dumps_json, loads_json)

        return create_engine(engine_url, json_serializer=dumps_json,
                             json_deserializer=loads_json)


def new_database(uri):
    """Drop the database at ``uri`` and create a brand new one. """
    destroy_database(uri)
    create_database(uri)


def destroy_database(uri):
    """Destroy the database at ``uri``, if it exists. """
    if database_exists(uri):
        drop_database(uri)


def database_exists(url):
    """Check if a database exists.


    sqlalchemy_utils.functions.database.database_exists

    :param url: A SQLAlchemy engine URL.

    Performs backend-specific testing to quickly determine if a database
    exists on the server. ::

        database_exists('postgres://postgres@localhost/name')  #=> False
        create_database('postgres://postgres@localhost/name')
        database_exists('postgres://postgres@localhost/name')  #=> True

    Supports checking against a constructed URL as well. ::

        engine = create_engine('postgres://postgres@localhost/name')
        database_exists(engine.url)  #=> False
        create_database(engine.url)
        database_exists(engine.url)  #=> True

    """
    from sqlalchemy.engine.url import make_url
    from sqlalchemy_utils.functions.orm import quote
    from copy import copy
    import sqlalchemy as sa

    url = copy(make_url(url))
    database = url.database
    if url.drivername.startswith('postgresql'):
        url.database = 'template1'
    else:
        url.database = None

    engine = sa.create_engine(url)

    try:
        if engine.dialect.name == 'postgresql':
            text = "SELECT 1 FROM pg_database WHERE datname='%s'" % database
            return bool(engine.execute(text).scalar())

        else:
            raise Exception("Only PostgreSQL is supported.")
    finally:
        engine.dispose()


def create_database(url, encoding='utf8'):
    """Issue the appropriate CREATE DATABASE statement.

    This is a modification of sqlalchemy_utils.functions.database.create_database
    since the latter one did not correctly work with SQLAlchemy and PostgreSQL.

    It was removed the template argument that was causing problems.

    :param url: A SQLAlchemy engine URL.
    :param encoding: The encoding to create the database as.


    It currently supports only PostgreSQL and the psycopg2 driver.
    """

    from sqlalchemy.engine.url import make_url
    from sqlalchemy_utils.functions.orm import quote
    from copy import copy
    import sqlalchemy as sa

    url = copy(make_url(url))

    database = url.database

    # A default PostgreSQL database to connect
    url.database = 'template1'
    # url.database = 'test_aiidadb_sqla3'

    engine = sa.create_engine(url)

    try:
        if engine.dialect.name == 'postgresql' and engine.driver == 'psycopg2':
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            engine.raw_connection().set_isolation_level(
                ISOLATION_LEVEL_AUTOCOMMIT
            )

            text = "CREATE DATABASE {0} ENCODING '{1}'".format(
                quote(engine, database),
                encoding
            )

            # text = "CREATE DATABASE {0}".format(
            #     quote(engine, database),
            #
            # )

            engine.execute(text)
            # print dir(engine)

            # conn = engine.connect()
            # conn.execute(text)
            # print dir(conn)
            #
            # conn.close()

        else:
            raise Exception("Only PostgreSQL with the psycopg2 driver is "
                            "supported.")
    finally:
        engine.dispose()
        # pass