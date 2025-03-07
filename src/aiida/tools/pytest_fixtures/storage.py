"""Fixtures providing resources for storage plugins."""

from __future__ import annotations

import pathlib
import typing as t
from uuid import uuid4

import pytest

if t.TYPE_CHECKING:
    from pgtest.pgtest import PGTest


class PostgresCluster:
    def __init__(self):
        # We initialize the cluster lazily
        self.cluster = None

    def _create(self):
        from pgtest.pgtest import PGTest

        try:
            self.cluster = PGTest()
        except OSError as e:
            raise RuntimeError('Could not initialize PostgreSQL cluster') from e

    def _close(self):
        if self.cluster is not None:
            self.cluster.close()

    def create_database(
        self,
        database_name: str | None = None,
        database_username: str | None = None,
        database_password: str | None = None,
    ) -> dict[str, str]:
        from aiida.manage.external.postgres import Postgres

        if self.cluster is None:
            self._create()

        postgres_config = {
            'database_engine': 'postgresql_psycopg',
            'database_name': database_name or str(uuid4()),
            'database_username': database_username or 'guest',
            'database_password': database_password or 'guest',
        }

        postgres = Postgres(interactive=False, quiet=True, dbinfo=self.cluster.dsn)  # type: ignore[union-attr]
        if not postgres.dbuser_exists(postgres_config['database_username']):
            postgres.create_dbuser(
                postgres_config['database_username'], postgres_config['database_password'], 'CREATEDB'
            )
        postgres.create_db(postgres_config['database_username'], postgres_config['database_name'])

        postgres_config['database_hostname'] = postgres.host_for_psycopg
        postgres_config['database_port'] = postgres.port_for_psycopg

        return postgres_config


@pytest.fixture(scope='session')
def postgres_cluster():
    """Create a temporary and isolated PostgreSQL cluster using ``pgtest`` and cleanup after the yield.

    :param database_name: Name of the database.
    :param database_username: Username to use for authentication.
    :param database_password: Password to use for authentication.
    :returns: Dictionary with parameters to connect to the PostgreSQL cluster.
    """

    cluster = PostgresCluster()
    yield cluster
    cluster._close()


@pytest.fixture(scope='session')
def config_psql_dos(
    tmp_path_factory: pytest.TempPathFactory,
    postgres_cluster: 'PGTest',
) -> t.Callable[[str | None, str | None, str | None], dict[str, t.Any]]:
    """Return a profile configuration for the :class:`~aiida.storage.psql_dos.backend.PsqlDosBackend`.

    The factory has the following signature to allow further configuring the database that is created:

    :param database_name: Name of the database to be created.
    :param database_username: Username to use for authentication.
    :param database_password: Password to use for authentication.
    :returns: The dictionary with the storage configuration for the ``core.psql_dos`` storage plugin.
    """

    def factory(
        database_name: str | None = None, database_username: str | None = None, database_password: str | None = None
    ) -> dict[str, t.Any]:
        storage_config: dict[str, t.Any] = postgres_cluster.create_database(
            database_name=database_name,
            database_username=database_username,
            database_password=database_password,
        )
        storage_config['repository_uri'] = pathlib.Path(f'{tmp_path_factory.mktemp("repository")}').as_uri()

        return storage_config

    return factory


@pytest.fixture(scope='session')
def config_sqlite_dos(
    tmp_path_factory: pytest.TempPathFactory,
) -> t.Callable[[str | pathlib.Path | None], dict[str, t.Any]]:
    """Return a profile configuration for the :class:`~aiida.storage.sqlite_dos.backend.SqliteDosStorage`.

    The factory has the following signature to allow further configuring the database that is created:

    :param filepath: Optional path to the sqlite database file.
    :returns: The dictionary with the storage configuration for the ``core.sqlite_dos`` storage plugin.
    """

    def factory(filepath: str | pathlib.Path | None = None) -> dict[str, t.Any]:
        return {'filepath': str(filepath or tmp_path_factory.mktemp('test_sqlite_dos_storage'))}

    return factory
