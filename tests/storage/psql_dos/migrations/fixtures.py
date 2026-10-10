###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
###########################################################################
"""Fixtures for PostgreSQL migration schema regression tests."""

from uuid import uuid4

import pytest
from pgtest.pgtest import PGTest

from aiida.manage.configuration import Profile


@pytest.fixture(scope='session')
def empty_pg_cluster():
    """Create an empty PostgreSQL cluster for the test session."""
    pg_cluster = PGTest()
    yield pg_cluster
    pg_cluster.close()


@pytest.fixture
def psql_dos_migration_profile(empty_pg_cluster: PGTest, tmp_path):
    """Return an uninitialised profile backed by a temporary PostgreSQL database."""
    import psycopg

    database_name = f'test_{uuid4().hex}'
    dsn = empty_pg_cluster.dsn.copy()
    dsn['dbname'] = dsn.pop('database')

    with psycopg.connect(**dsn, autocommit=True) as connection:
        connection.execute(f"CREATE DATABASE {database_name} ENCODING 'utf8';")

    profile = Profile(
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

    yield profile

    with psycopg.connect(**dsn, autocommit=True) as connection:
        connection.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{database_name}';")
        connection.execute(f'DROP DATABASE {database_name};')
