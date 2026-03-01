###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the migration engine (Alembic) as well as for the AiiDA migrations for SQLAlchemy."""

from uuid import uuid4

import pytest
from pgtest.pgtest import PGTest
from sqlalchemy import text

from aiida.manage.configuration import Profile
from aiida.storage.psql_dos.migrator import PsqlDosMigrator
from aiida.storage.psql_dos.utils import create_sqlalchemy_engine


@pytest.fixture(scope='session')
def empty_pg_cluster():
    """Create an empty PostgreSQL cluster, for the duration of the session."""
    pg_cluster = PGTest()
    yield pg_cluster
    pg_cluster.close()


@pytest.fixture
def uninitialised_profile(empty_pg_cluster: PGTest, tmp_path):
    """Create a profile attached to an empty database and repository folder."""
    import psycopg

    database_name = f'test_{uuid4().hex}'
    dsn = empty_pg_cluster.dsn
    dsn['dbname'] = dsn.pop('database')

    conn = None
    try:
        conn = psycopg.connect(**dsn)
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE {database_name} ENCODING 'utf8';")
    finally:
        if conn:
            conn.close()

    yield Profile(
        'test_migrate',
        {
            'test_profile': True,
            'storage': {
                'backend': 'core.psql_dos',
                'config': {
                    'database_engine': 'postgresql_psycopg',
                    'database_port': empty_pg_cluster.port,
                    'database_hostname': empty_pg_cluster.dsn['host'],
                    'database_name': database_name,
                    'database_password': '',
                    'database_username': empty_pg_cluster.username,
                    'repository_uri': f'file:///{tmp_path}',
                },
            },
            'process_control': {'backend': 'null', 'config': {}},
        },
    )

    conn = None
    try:
        conn = psycopg.connect(**dsn)
        conn.autocommit = True
        with conn.cursor() as cursor:
            # note after postgresql 13 you can use 'DROP DATABASE name WITH (FORCE)'
            # but for now, we first close all possible open connections to the database, before dropping it
            # see: https://dba.stackexchange.com/questions/11893/force-drop-db-while-others-may-be-connected
            cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{database_name}';")
            cursor.execute(f'DROP DATABASE {database_name};')
    finally:
        if conn:
            conn.close()


@pytest.fixture()
def perform_migrations(uninitialised_profile):
    """A fixture to setup a database for migration tests."""
    yield PsqlDosMigrator(uninitialised_profile)


def _generate_column_schema(profile: Profile) -> dict:
    """Create a dict containing all tables and fields of AiiDA tables."""
    # see https://www.postgresql.org/docs/9.1/infoschema-columns.html
    with create_sqlalchemy_engine(profile.storage_config).connect() as conn:
        table_data = conn.execute(
            text(
                'SELECT table_name,column_name,data_type,is_nullable,column_default,character_maximum_length '
                'FROM information_schema.columns '
                "WHERE table_schema = 'public' AND table_name LIKE 'db_%';"
            )
        )
    data = {}
    for tbl_name, col_name, data_type, is_nullable, column_default, char_max_length in table_data:
        data.setdefault(tbl_name, {})[col_name] = {
            'data_type': data_type,
            'is_nullable': is_nullable.upper() == 'YES',
            'default': column_default,
        }
        if char_max_length:
            data[tbl_name][col_name]['max_length'] = char_max_length

    return data


def _generate_constraints_schema(profile: Profile) -> dict:
    """Create a dict containing constraints of AiiDA tables."""
    # see https://www.postgresql.org/docs/9.1/catalog-pg-constraint.html
    data = {}
    for cname, ctype in (('primary_key', 'p'), ('unique', 'u')):
        with create_sqlalchemy_engine(profile.storage_config).connect() as conn:
            constaints_data = conn.execute(
                text(
                    'SELECT tbl.relname,c.conname,ARRAY_AGG(a.attname) FROM pg_constraint AS c '
                    'INNER JOIN pg_class AS tbl ON tbl.oid = c.conrelid '
                    'INNER JOIN pg_attribute AS a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey) '
                    f"WHERE c.contype='{ctype}' AND tbl.relname LIKE 'db_%' "
                    'GROUP BY tbl.relname,c.conname;'
                )
            )
            for tbl_name, name, col_names in sorted(constaints_data):
                data.setdefault(cname, {}).setdefault(tbl_name, {})[name] = sorted(col_names)
    return data


def _generate_fkey_schema(profile: Profile) -> dict:
    """Create a dict containing foreign keys of AiiDA tables."""
    # see https://www.postgresql.org/docs/9.1/catalog-pg-constraint.html
    data = {}
    with create_sqlalchemy_engine(profile.storage_config).connect() as conn:
        constaints_data = conn.execute(
            text(
                'SELECT conrelid::regclass,conname, pg_get_constraintdef(oid) FROM pg_constraint '
                "WHERE contype='f' AND conrelid::regclass::text LIKE 'db_%' "
                "AND connamespace='public'::regnamespace "
                'ORDER BY conrelid::regclass::text, contype DESC;'
            )
        )
        for tbl_name, name, description in sorted(constaints_data):
            data.setdefault(tbl_name, {})[name] = description
    return data


def _generate_index_schema(profile: Profile) -> dict:
    """Create a dict containing indexes of AiiDA tables."""
    # see https://www.postgresql.org/docs/9.1/view-pg-indexes.html
    with create_sqlalchemy_engine(profile.storage_config).connect() as conn:
        index_data = conn.execute(
            text(
                'SELECT tablename,indexname,indexdef FROM pg_indexes '
                "WHERE tablename LIKE 'db_%' "
                'ORDER BY tablename,indexname;'
            )
        )
    data = {}
    for tbl_name, name, definition in sorted(index_data):
        data.setdefault(tbl_name, {})[name] = definition
    return data


@pytest.fixture
def reflect_schema():
    """A fixture to generate the schema of AiiDA tables for a given profile."""

    def _generate_schema(profile: Profile) -> dict:
        """Create a dict containing all tables and fields of AiiDA tables."""
        return {
            'columns': _generate_column_schema(profile),
            'constraints': _generate_constraints_schema(profile),
            'foreign_keys': _generate_fkey_schema(profile),
            'indexes': _generate_index_schema(profile),
        }

    return _generate_schema
