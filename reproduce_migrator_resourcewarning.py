import tempfile
from uuid import uuid4

import psycopg
from pgtest.pgtest import PGTest

from aiida.manage.configuration import Profile
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def main():
    # Start a temporary PostgreSQL cluster
    pg_cluster = PGTest()

    database_name = f'test_{uuid4().hex}'
    dsn = pg_cluster.dsn.copy()
    dsn['dbname'] = dsn.pop('database')

    # Create empty database
    with psycopg.connect(**dsn) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE {database_name} TEMPLATE template0 ENCODING 'UTF8';")

    # Temporary repository directory
    with tempfile.TemporaryDirectory() as repo_dir:
        profile = Profile(
            'reproducer_profile',
            {
                'test_profile': True,
                'storage': {
                    'backend': 'core.psql_dos',
                    'config': {
                        'database_engine': 'postgresql_psycopg',
                        'database_name': database_name,
                        'database_username': pg_cluster.username,
                        'database_password': '',
                        'database_hostname': dsn['host'],
                        'database_port': pg_cluster.port,
                        'repository_uri': f'file:///{repo_dir}',
                    },
                },
                'process_control': {'backend': 'null', 'config': {}},
            },
        )

        # 🔑 This is the part under test
        with PsqlDosMigrator(profile) as migrator:
            migrator.get_schema_version_head()
            migrator.get_schema_version_profile()

    # Cleanup database
    with psycopg.connect(**dsn) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                f'SELECT pg_terminate_backend(pid) ' f"FROM pg_stat_activity WHERE datname = '{database_name}';"
            )
            cursor.execute(f'DROP DATABASE {database_name};')

    pg_cluster.close()
    print('Reproducer finished cleanly.')


if __name__ == '__main__':
    main()
