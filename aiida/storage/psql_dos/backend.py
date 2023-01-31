# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SqlAlchemy implementation of `aiida.orm.implementation.backends.Backend`."""
# pylint: disable=missing-function-docstring
from contextlib import contextmanager, nullcontext
import functools
import gc
import pathlib
from typing import TYPE_CHECKING, Iterator, List, Optional, Sequence, Set, Union

from disk_objectstore import Container
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from aiida.common.exceptions import ClosedStorage, ConfigurationError, IntegrityError
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

CONTAINER_DEFAULTS: dict = {
    'pack_size_target': 4 * 1024 * 1024 * 1024,
    'loose_prefix_len': 2,
    'hash_type': 'sha256',
    'compression_algorithm': 'zlib+1'
}


def get_filepath_container(profile: Profile) -> pathlib.Path:
    """Return the filepath of the disk-object store container."""
    from urllib.parse import urlparse

    try:
        parts = urlparse(profile.storage_config['repository_uri'])
    except KeyError:
        raise KeyError(f'invalid profile {profile.name}: `repository_uri` not defined in `storage.config`.')

    if parts.scheme != 'file':
        raise ConfigurationError(
            f'invalid profile {profile.name}: `storage.config.repository_uri` does not start with `file://`.'
        )

    filepath = pathlib.Path(parts.path)

    if not filepath.is_absolute():
        raise ConfigurationError(f'invalid profile {profile.name}: `storage.config.repository_uri` is not absolute')

    return filepath.expanduser() / 'container'


class PsqlDosBackend(StorageBackend):  # pylint: disable=too-many-public-methods
    """An AiiDA storage backend that stores data in a PostgreSQL database and disk-objectstore repository.

    Note, there were originally two such backends, `sqlalchemy` and `django`.
    The `django` backend was removed, to consolidate access to this storage.
    """

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
        self._db_url = self.get_session().get_bind().url  # type: ignore

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
        engine = create_sqlalchemy_engine(self._profile.storage_config)  # type: ignore
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
        # pylint: disable=no-member
        engine = self._session_factory.bind
        if engine is not None:
            engine.dispose()  # type: ignore
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

            # First clear the contents of the database
            with self.transaction() as session:

                # Close the session otherwise the ``delete_tables`` call will hang as there will be an open connection
                # to the PostgreSQL server and it will block the deletion and the command will hang.
                self.get_session().close()
                exclude_tables = [migrator.alembic_version_tbl_name, 'db_dbsetting']
                migrator.delete_all_tables(exclude_tables=exclude_tables)

                # Clear out all references to database model instances which are now invalid.
                session.expunge_all()

            # Now reset and reinitialise the repository
            migrator.reset_repository()
            migrator.initialise_repository()
            repository_uuid = migrator.get_repository_uuid()

            with self.transaction():
                session.execute(
                    DbSetting.__table__.update().where(DbSetting.key == REPOSITORY_UUID_KEY
                                                       ).values(val=repository_uuid)
                )

    def get_repository(self) -> 'DiskObjectStoreRepositoryBackend':
        from aiida.repository.backend import DiskObjectStoreRepositoryBackend
        container = Container(str(get_filepath_container(self.profile)))
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
            with session.begin_nested():
                yield session
            session.commit()
        else:
            with session.begin():
                with session.begin_nested():
                    yield session

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
        with (nullcontext() if self.in_transaction else self.transaction()):
            session.bulk_insert_mappings(mapper, rows, render_nulls=True, return_defaults=True)
        return [row['id'] for row in rows]

    def bulk_update(self, entity_type: EntityTypes, rows: List[dict]) -> None:  # pylint: disable=no-self-use
        mapper, keys = self._get_mapper_from_entity(entity_type, True)
        if not rows:
            return None
        for row in rows:
            if 'id' not in row:
                raise IntegrityError(f"'id' field not given for {entity_type}: {set(row)}")
            if not keys.issuperset(row):
                raise IntegrityError(f'Incorrect fields given for {entity_type}: {set(row)} not subset of {keys}')
        session = self.get_session()
        with (nullcontext() if self.in_transaction else self.transaction()):
            session.bulk_update_mappings(mapper, rows)

    def delete_nodes_and_connections(self, pks_to_delete: Sequence[int]) -> None:  # pylint: disable=no-self-use
        # pylint: disable=no-value-for-parameter
        from aiida.storage.psql_dos.models.group import DbGroupNode
        from aiida.storage.psql_dos.models.node import DbLink, DbNode

        if not self.in_transaction:
            raise AssertionError('Cannot delete nodes and links outside a transaction')

        session = self.get_session()
        # Delete the membership of these nodes to groups.
        session.query(DbGroupNode).filter(DbGroupNode.dbnode_id.in_(list(pks_to_delete))
                                          ).delete(synchronize_session='fetch')
        # Delete the links coming out of the nodes marked for deletion.
        session.query(DbLink).filter(DbLink.input_id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
        # Delete the links pointing to the nodes marked for deletion.
        session.query(DbLink).filter(DbLink.output_id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
        # Delete the actual nodes
        session.query(DbNode).filter(DbNode.id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')

    def get_backend_entity(self, model: base.Base) -> BackendEntity:
        """
        Return the backend entity that corresponds to the given Model instance

        :param model: the ORM model instance to promote to a backend instance
        :return: the backend entity corresponding to the given model
        """
        return convert.get_backend_entity(model, self)

    def set_global_variable(
        self, key: str, value: Union[None, str, int, float], description: Optional[str] = None, overwrite=True
    ) -> None:
        from aiida.storage.psql_dos.models.settings import DbSetting

        session = self.get_session()
        with (nullcontext() if self.in_transaction else self.transaction()):
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
        with (nullcontext() if self.in_transaction else self.transaction()):
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
            maintenance_context = nullcontext  # type: ignore

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
        keyset_database = set(orm.Node.collection(self).iter_repo_keys())

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
