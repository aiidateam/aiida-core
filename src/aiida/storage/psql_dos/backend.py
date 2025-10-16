###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SqlAlchemy implementation of `aiida.orm.implementation.backends.Backend`."""

import functools
import gc
import pathlib
from contextlib import contextmanager, nullcontext
from typing import TYPE_CHECKING, Iterator, List, Optional, Sequence, Set, Union

from disk_objectstore import Container, backup_utils
from pydantic import BaseModel, Field
from sqlalchemy import column, insert, update
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from aiida.common import exceptions
from aiida.common.exceptions import ClosedStorage, ConfigurationError, IntegrityError
from aiida.common.log import AIIDA_LOGGER
from aiida.manage.configuration.profile import Profile
from aiida.orm.entities import EntityTypes
from aiida.orm.implementation import BackendEntity, StorageBackend
from aiida.storage.log import STORAGE_LOGGER
from aiida.storage.psql_dos.migrator import REPOSITORY_UUID_KEY, PsqlDosMigrator
from aiida.storage.psql_dos.models import base

from .orm import authinfos, comments, computers, convert, groups, logs, nodes, querybuilder, users

if TYPE_CHECKING:
    from aiida.repository.backend import DiskObjectStoreRepositoryBackend

__all__ = ('PsqlDosBackend',)

LOGGER = AIIDA_LOGGER.getChild(__file__)
CONTAINER_DEFAULTS: dict = {
    'pack_size_target': 4 * 1024 * 1024 * 1024,
    'loose_prefix_len': 2,
    'hash_type': 'sha256',
    'compression_algorithm': 'zlib+1',
}


def get_filepath_container(profile: Profile) -> pathlib.Path:
    """Return the filepath of the disk-object store container."""
    from urllib.parse import urlparse
    from urllib.request import url2pathname

    try:
        parts = urlparse(profile.storage_config['repository_uri'])
    except KeyError:
        raise KeyError(f'invalid profile {profile.name}: `repository_uri` not defined in `storage.config`.')

    if parts.scheme != 'file':
        raise ConfigurationError(
            f'invalid profile {profile.name}: `storage.config.repository_uri` does not start with `file://`.'
        )

    filepath = pathlib.Path(url2pathname(parts.path))

    if not filepath.is_absolute():
        raise ConfigurationError(f'invalid profile {profile.name}: `storage.config.repository_uri` is not absolute')

    return filepath.expanduser() / 'container'


class PsqlDosBackend(StorageBackend):
    """An AiiDA storage backend that stores data in a PostgreSQL database and disk-objectstore repository.

    Note, there were originally two such backends, `sqlalchemy` and `django`.
    The `django` backend was removed, to consolidate access to this storage.
    """

    class Model(BaseModel, defer_build=True):
        """Model describing required information to configure an instance of the storage."""

        database_engine: str = Field(
            title='PostgreSQL engine',
            description='The engine to use to connect to the database.',
            default='postgresql_psycopg',
        )
        database_hostname: str = Field(
            title='PostgreSQL hostname', description='The hostname of the PostgreSQL server.', default='localhost'
        )
        database_port: int = Field(
            title='PostgreSQL port', description='The port of the PostgreSQL server.', default=5432
        )
        database_username: str = Field(
            title='PostgreSQL username', description='The username with which to connect to the PostgreSQL server.'
        )
        database_password: str = Field(
            title='PostgreSQL password', description='The password with which to connect to the PostgreSQL server.'
        )
        database_name: str = Field(
            title='PostgreSQL database name', description='The name of the database in the PostgreSQL server.'
        )
        repository_uri: str = Field(
            title='File repository URI',
            description='URI to the file repository.',
        )

    migrator = PsqlDosMigrator

    @classmethod
    def version_head(cls) -> str:
        return cls.migrator.get_schema_version_head()

    @classmethod
    def version_profile(cls, profile: Profile) -> Optional[str]:
        with cls.migrator_context(profile) as migrator:
            return migrator.get_schema_version_profile(check_legacy=True)

    @classmethod
    def initialise(cls, profile: Profile, reset: bool = False) -> bool:
        with cls.migrator_context(profile) as migrator:
            return migrator.initialise(reset=reset)

    @classmethod
    def migrate(cls, profile: Profile) -> None:
        with cls.migrator_context(profile) as migrator:
            migrator.migrate()

    @classmethod
    @contextmanager
    def migrator_context(cls, profile: Profile):
        migrator = cls.migrator(profile)
        try:
            yield migrator
        finally:
            migrator.close()

    def __init__(self, profile: Profile) -> None:
        super().__init__(profile)

        # check that the storage is reachable and at the correct version
        with self.migrator_context(profile) as migrator:
            migrator.validate_storage()

        self._session_factory: Optional[scoped_session] = None
        self._initialise_session()
        # save the URL of the database, for use in the __str__ method
        self._db_url = self.get_session().get_bind().url  # type: ignore[union-attr]

        self._authinfos = authinfos.SqlaAuthInfoCollection(self)
        self._comments = comments.SqlaCommentCollection(self)
        self._computers = computers.SqlaComputerCollection(self)
        self._groups = groups.SqlaGroupCollection(self)
        self._logs = logs.SqlaLogCollection(self)
        self._nodes = nodes.SqlaNodeCollection(self)
        self._users = users.SqlaUserCollection(self)

    @property
    def is_closed(self) -> bool:
        return self._session_factory is None

    def __str__(self) -> str:
        state = 'closed' if self.is_closed else 'open'
        return f'Storage for {self.profile.name!r} [{state}] @ {self._db_url!r} / {self.get_repository()}'

    def _initialise_session(self):
        """Initialise the SQLAlchemy session factory.

        Only one session factory is ever associated with a given class instance,
        i.e. once the instance is closed, it cannot be reopened.

        The session factory, returns a session that is bound to the current thread.
        Multi-thread support is currently required by the REST API.
        Although, in the future, we may want to move the multi-thread handling to higher in the AiiDA stack.
        """
        from aiida.storage.psql_dos.utils import create_sqlalchemy_engine

        engine = create_sqlalchemy_engine(self._profile.storage_config)  # type: ignore[arg-type]
        self._session_factory = scoped_session(sessionmaker(bind=engine, future=True, expire_on_commit=True))

    def get_session(self) -> Session:
        """Return an SQLAlchemy session bound to the current thread."""
        if self._session_factory is None:
            raise ClosedStorage(str(self))
        return self._session_factory()

    def close(self) -> None:
        if self._session_factory is None:
            return  # the instance is already closed, and so this is a no-op
        # close the connection

        engine = self._session_factory.bind
        if engine is not None:
            engine.dispose()  # type: ignore[union-attr]
        self._session_factory.expunge_all()
        self._session_factory.close()
        self._session_factory = None

        # Without this, sqlalchemy keeps a weakref to a session
        # in sqlalchemy.orm.session._sessions
        gc.collect()

    def _clear(self) -> None:
        from aiida.storage.psql_dos.models.settings import DbSetting

        super()._clear()

        with self.migrator_context(self._profile) as migrator:
            # Close the session otherwise the ``delete_tables`` call will hang as there will be an open connection
            # to the PostgreSQL server and it will block the deletion and the command will hang.
            self.get_session().close()
            exclude_tables = [migrator.alembic_version_tbl_name, 'db_dbsetting']
            migrator.delete_all_tables(exclude_tables=exclude_tables)

            # Clear out all references to database model instances which are now invalid.
            self.get_session().expunge_all()

            # Now reset and reinitialise the repository
            migrator.reset_repository()
            migrator.initialise_repository()
            repository_uuid = migrator.get_repository_uuid()

            with self.transaction() as session:
                session.execute(
                    DbSetting.__table__.update().where(DbSetting.key == REPOSITORY_UUID_KEY).values(val=repository_uuid)
                )

    def get_repository(self) -> 'DiskObjectStoreRepositoryBackend':
        from aiida.repository.backend import DiskObjectStoreRepositoryBackend

        container = Container(get_filepath_container(self.profile))
        return DiskObjectStoreRepositoryBackend(container=container)

    @property
    def authinfos(self):
        return self._authinfos

    @property
    def comments(self):
        return self._comments

    @property
    def computers(self):
        return self._computers

    @property
    def groups(self):
        return self._groups

    @property
    def logs(self):
        return self._logs

    @property
    def nodes(self):
        return self._nodes

    def query(self):
        return querybuilder.SqlaQueryBuilder(self)

    @property
    def users(self):
        return self._users

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        """Open a transaction to be used as a context manager.

        If there is an exception within the context then the changes will be rolled back and the state will be as before
        entering. Transactions can be nested.
        """
        session = self.get_session()
        if session.in_transaction():
            with session.begin_nested() as savepoint:
                yield session
                savepoint.commit()
            session.commit()
        else:
            with session.begin():
                with session.begin_nested() as savepoint:
                    yield session
                    savepoint.commit()

    @property
    def in_transaction(self) -> bool:
        return self.get_session().in_nested_transaction()

    @staticmethod
    @functools.lru_cache(maxsize=18)
    def _get_mapper_from_entity(entity_type: EntityTypes, with_pk: bool):
        """Return the Sqlalchemy mapper and fields corresponding to the given entity.

        :param with_pk: if True, the fields returned will include the primary key
        """
        from sqlalchemy import inspect

        from aiida.storage.psql_dos.models.authinfo import DbAuthInfo
        from aiida.storage.psql_dos.models.comment import DbComment
        from aiida.storage.psql_dos.models.computer import DbComputer
        from aiida.storage.psql_dos.models.group import DbGroup, DbGroupNode
        from aiida.storage.psql_dos.models.log import DbLog
        from aiida.storage.psql_dos.models.node import DbLink, DbNode
        from aiida.storage.psql_dos.models.user import DbUser

        model = {
            EntityTypes.AUTHINFO: DbAuthInfo,
            EntityTypes.COMMENT: DbComment,
            EntityTypes.COMPUTER: DbComputer,
            EntityTypes.GROUP: DbGroup,
            EntityTypes.LOG: DbLog,
            EntityTypes.NODE: DbNode,
            EntityTypes.USER: DbUser,
            EntityTypes.LINK: DbLink,
            EntityTypes.GROUP_NODE: DbGroupNode,
        }[entity_type]
        mapper = inspect(model).mapper
        keys = {key for key, col in mapper.c.items() if with_pk or col not in mapper.primary_key}
        return mapper, keys

    def bulk_insert(self, entity_type: EntityTypes, rows: List[dict], allow_defaults: bool = False) -> List[int]:
        mapper, keys = self._get_mapper_from_entity(entity_type, False)
        if not rows:
            return []
        if entity_type in (EntityTypes.COMPUTER, EntityTypes.LOG, EntityTypes.AUTHINFO):
            for row in rows:
                row['_metadata'] = row.pop('metadata')
        if allow_defaults:
            for row in rows:
                if not keys.issuperset(row):
                    raise IntegrityError(f'Incorrect fields given for {entity_type}: {set(row)} not subset of {keys}')
        else:
            for row in rows:
                if set(row) != keys:
                    raise IntegrityError(f'Incorrect fields given for {entity_type}: {set(row)} != {keys}')
        # note for postgresql+psycopg2 we could also use `save_all` + `flush` with minimal performance degradation, see
        # https://docs.sqlalchemy.org/en/14/changelog/migration_14.html#orm-batch-inserts-with-psycopg2-now-batch-statements-with-returning-in-most-cases
        # by contrast, in sqlite, bulk_insert is faster: https://docs.sqlalchemy.org/en/14/faq/performance.html
        session = self.get_session()
        with nullcontext() if self.in_transaction else self.transaction():
            result = session.execute(insert(mapper).returning(mapper, column('id')), rows).fetchall()
        return [row.id for row in result]

    def bulk_update(self, entity_type: EntityTypes, rows: List[dict]) -> None:
        mapper, keys = self._get_mapper_from_entity(entity_type, True)
        if not rows:
            return None
        for row in rows:
            if 'id' not in row:
                raise IntegrityError(f"'id' field not given for {entity_type}: {set(row)}")
            if not keys.issuperset(row):
                raise IntegrityError(f'Incorrect fields given for {entity_type}: {set(row)} not subset of {keys}')
        session = self.get_session()
        with nullcontext() if self.in_transaction else self.transaction():
            session.execute(update(mapper), rows)

    def delete(self, delete_database_user: bool = False) -> None:
        """Delete the storage and all the data.

        :param delete_database_user: Also delete the database user. This is ``False`` by default because the user may be
            used by other databases.
        """
        import shutil

        from aiida.manage.external.postgres import Postgres

        profile = self.profile
        config = profile.storage_config
        postgres = Postgres.from_profile(self.profile)
        repository = get_filepath_container(profile).parent

        if repository.exists():
            shutil.rmtree(repository)
            LOGGER.report(f'Deleted repository at `{repository}`.')

        if postgres.db_exists(config['database_name']):
            postgres.drop_db(config['database_name'])
            LOGGER.report(f'Deleted database `{config["database_name"]}`.')

        if delete_database_user and postgres.dbuser_exists(config['database_username']):
            postgres.drop_dbuser(config['database_username'])
            LOGGER.report(f'Deleted database user `{config["database_username"]}`.')

    def delete_nodes_and_connections(self, pks_to_delete: Sequence[int]) -> None:
        from aiida.storage.psql_dos.models.group import DbGroupNode
        from aiida.storage.psql_dos.models.node import DbLink, DbNode

        if not self.in_transaction:
            raise AssertionError('Cannot delete nodes and links outside a transaction')

        session = self.get_session()
        # Delete the membership of these nodes to groups.
        session.query(DbGroupNode).filter(DbGroupNode.dbnode_id.in_(list(pks_to_delete))).delete(
            synchronize_session='fetch'
        )
        # Delete the links coming out of the nodes marked for deletion.
        session.query(DbLink).filter(DbLink.input_id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
        # Delete the links pointing to the nodes marked for deletion.
        session.query(DbLink).filter(DbLink.output_id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
        # Delete the actual nodes
        session.query(DbNode).filter(DbNode.id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')

    def get_backend_entity(self, model: base.Base) -> BackendEntity:
        """Return the backend entity that corresponds to the given Model instance

        :param model: the ORM model instance to promote to a backend instance
        :return: the backend entity corresponding to the given model
        """
        return convert.get_backend_entity(model, self)

    def set_global_variable(
        self, key: str, value: Union[None, str, int, float], description: Optional[str] = None, overwrite=True
    ) -> None:
        from aiida.storage.psql_dos.models.settings import DbSetting

        session = self.get_session()
        with nullcontext() if self.in_transaction else self.transaction():
            if session.query(DbSetting).filter(DbSetting.key == key).count():
                if overwrite:
                    session.query(DbSetting).filter(DbSetting.key == key).update(dict(val=value))
                else:
                    raise ValueError(f'The setting {key} already exists')
            else:
                session.add(DbSetting(key=key, val=value, description=description or ''))

    def get_global_variable(self, key: str) -> Union[None, str, int, float]:
        from aiida.storage.psql_dos.models.settings import DbSetting

        session = self.get_session()
        with nullcontext() if self.in_transaction else self.transaction():
            setting = session.query(DbSetting).filter(DbSetting.key == key).one_or_none()
            if setting is None:
                raise KeyError(f'No setting found with key {key}')
            return setting.val

    def maintain(self, full: bool = False, dry_run: bool = False, **kwargs) -> None:
        from aiida.manage.profile_access import ProfileAccessManager

        repository = self.get_repository()

        if full:
            maintenance_context = ProfileAccessManager(self._profile).lock
        else:
            maintenance_context = nullcontext  # type: ignore[assignment]

        with maintenance_context():
            unreferenced_objects = self.get_unreferenced_keyset()
            STORAGE_LOGGER.info(f'Deleting {len(unreferenced_objects)} unreferenced objects ...')
            if not dry_run:
                repository.delete_objects(list(unreferenced_objects))

            STORAGE_LOGGER.info('Starting repository-specific operations ...')
            repository.maintain(live=not full, dry_run=dry_run, **kwargs)

    def get_unreferenced_keyset(self, check_consistency: bool = True) -> Set[str]:
        """Returns the keyset of objects that exist in the repository but are not tracked by AiiDA.

        This should be all the soft-deleted files.

        :param check_consistency:
            toggle for a check that raises if there are references in the database with no actual object in the
            underlying repository.

        :return:
            a set with all the objects in the underlying repository that are not referenced in the database.
        """
        from aiida import orm

        STORAGE_LOGGER.info('Obtaining unreferenced object keys ...')

        repository = self.get_repository()

        keyset_repository = set(repository.list_objects())
        keyset_database = set(orm.Node.get_collection(self).iter_repo_keys())

        if check_consistency:
            keyset_missing = keyset_database - keyset_repository
            if len(keyset_missing) > 0:
                raise RuntimeError(
                    'There are objects referenced in the database that are not present in the repository. Aborting!'
                )

        return keyset_repository - keyset_database

    def get_info(self, detailed: bool = False) -> dict:
        results = super().get_info(detailed=detailed)
        results['repository'] = self.get_repository().get_info(detailed)
        return results

    def _backup_storage(
        self,
        manager: backup_utils.BackupManager,
        path: pathlib.Path,
        prev_backup: Optional[pathlib.Path] = None,
    ) -> None:
        """Create a backup of the postgres database and disk-objectstore to the provided path.

        :param manager:
            BackupManager from backup_utils containing utilities such as for calling the rsync.

        :param path:
            Path to where the backup will be created.

        :param prev_backup:
            Path to the previous backup. Rsync calls will be hard-linked to this path, making the backup
            incremental and efficient.
        """
        import os
        import shutil
        import subprocess
        import tempfile

        STORAGE_LOGGER.report('Starting backup...')

        # This command calls `rsync` and `pg_dump` executables. check that they are in PATH
        for exe in ['rsync', 'pg_dump']:
            if shutil.which(exe) is None:
                raise exceptions.StorageBackupError(f"Required executable '{exe}' not found in PATH, please add it.")

        cfg = self._profile.storage_config
        container = Container(get_filepath_container(self.profile))

        # step 1: first run the storage maintenance version that can safely be performed while aiida is running
        STORAGE_LOGGER.report('Running basic maintenance...')
        self.maintain(full=False, compress=False)

        # step 2: dump the PostgreSQL database into a temporary directory
        STORAGE_LOGGER.report('Backing up PostgreSQL...')
        pg_dump_exe = 'pg_dump'
        with tempfile.TemporaryDirectory() as temp_dir_name:
            psql_temp_loc = pathlib.Path(temp_dir_name) / 'db.psql'

            env = os.environ.copy()
            env['PGPASSWORD'] = cfg['database_password']
            cmd = [
                pg_dump_exe,
                f'--host={cfg["database_hostname"]}',
                f'--port={cfg["database_port"]}',
                f'--dbname={cfg["database_name"]}',
                f'--username={cfg["database_username"]}',
                '--no-password',
                '--format=p',
                f'--file={psql_temp_loc!s}',
            ]
            try:
                subprocess.run(cmd, check=True, env=env)
            except subprocess.CalledProcessError as exc:
                raise backup_utils.BackupError(f'pg_dump: {exc}')

            if psql_temp_loc.is_file():
                STORAGE_LOGGER.info(f'Dumped the PostgreSQL database to {psql_temp_loc!s}')
            else:
                raise backup_utils.BackupError(f"'{psql_temp_loc!s}' was not created.")

            # step 3: transfer the PostgreSQL database file
            manager.call_rsync(psql_temp_loc, path, link_dest=prev_backup, dest_trailing_slash=True)

        # step 4: back up the disk-objectstore
        STORAGE_LOGGER.report('Backing up DOS container...')
        backup_utils.backup_container(
            manager, container, path / 'container', prev_backup=prev_backup / 'container' if prev_backup else None
        )

    def _backup(
        self,
        dest: str,
        keep: Optional[int] = None,
    ):
        try:
            backup_manager = backup_utils.BackupManager(dest, keep=keep)
            backup_manager.backup_auto_folders(lambda path, prev: self._backup_storage(backup_manager, path, prev))
        except backup_utils.BackupError as exc:
            raise exceptions.StorageBackupError(*exc.args) from exc
