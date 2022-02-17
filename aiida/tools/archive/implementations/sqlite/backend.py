# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The table models are dynamically generated from the sqlalchemy backend models."""
from contextlib import contextmanager
from datetime import datetime
from functools import singledispatch
from pathlib import Path
import tempfile
from typing import BinaryIO, Iterable, Iterator, List, Optional, Sequence, Tuple, Type, cast
import zipfile
from zipfile import ZipFile

from archive_path import extract_file_in_zip
import pytz
from sqlalchemy import CHAR, Text, orm, types
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql.schema import Table

# we need to import all models, to ensure they are loaded on the SQLA Metadata
from aiida.backends.sqlalchemy.models import authinfo, base, comment, computer, group, log, node, user
from aiida.common.exceptions import UnreachableStorage
from aiida.manage import Profile
from aiida.orm.entities import EntityTypes
from aiida.orm.implementation.backends import Backend as BackendAbstract
from aiida.orm.implementation.sqlalchemy import authinfos, comments, computers, entities, groups, logs, nodes, users
from aiida.orm.implementation.sqlalchemy.querybuilder import SqlaQueryBuilder
from aiida.orm.implementation.sqlalchemy.utils import ModelWrapper
from aiida.repository.backend.abstract import AbstractRepositoryBackend
from aiida.tools.archive.exceptions import ArchiveClosedError, CorruptArchive, ReadOnlyError

from .common import DB_FILENAME, REPO_FOLDER, create_sqla_engine


class SqliteModel:
    """Represent a row in an sqlite database table"""

    def __repr__(self) -> str:
        """Return a representation of the row columns"""
        string = f'<{self.__class__.__name__}'
        for col in self.__table__.columns:  # type: ignore[attr-defined] # pylint: disable=no-member
            # don't include columns with potentially large values
            if isinstance(col.type, (JSON, Text)):
                continue
            string += f' {col.name}={getattr(self, col.name)}'
        return string + '>'


class TZDateTime(types.TypeDecorator):  # pylint: disable=abstract-method
    """A timezone naive UTC ``DateTime`` implementation for SQLite.

    see: https://docs.sqlalchemy.org/en/14/core/custom_types.html#store-timezone-aware-timestamps-as-timezone-naive-utc
    """
    impl = types.DateTime
    cache_ok = True

    def process_bind_param(self, value: Optional[datetime], dialect):
        """Process before writing to database."""
        if value is None:
            return value
        if value.tzinfo is None:
            value = value.astimezone(pytz.utc)
        value = value.astimezone(pytz.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value: Optional[datetime], dialect):
        """Process when returning from database."""
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=pytz.utc)
        return value.astimezone(pytz.utc)


ArchiveDbBase = orm.declarative_base(cls=SqliteModel, name='SqliteModel')


def pg_to_sqlite(pg_table: Table):
    """Convert a model intended for PostGreSQL to one compatible with SQLite"""
    new = pg_table.to_metadata(ArchiveDbBase.metadata)
    for column in new.columns:
        if isinstance(column.type, UUID):
            column.type = CHAR(32)
        elif isinstance(column.type, types.DateTime):
            column.type = TZDateTime()
        elif isinstance(column.type, JSONB):
            column.type = JSON()
    return new


def create_orm_cls(klass: base.Base) -> ArchiveDbBase:
    """Create an ORM class from an existing table in the declarative meta"""
    tbl = ArchiveDbBase.metadata.tables[klass.__tablename__]
    return type(  # type: ignore[return-value]
        klass.__name__,
        (ArchiveDbBase,),
        {
            '__tablename__': tbl.name,
            '__table__': tbl,
            **{col.name if col.name != 'metadata' else '_metadata': col for col in tbl.columns},
        },
    )


for table in base.Base.metadata.sorted_tables:
    pg_to_sqlite(table)

DbUser = create_orm_cls(user.DbUser)
DbComputer = create_orm_cls(computer.DbComputer)
DbAuthInfo = create_orm_cls(authinfo.DbAuthInfo)
DbGroup = create_orm_cls(group.DbGroup)
DbNode = create_orm_cls(node.DbNode)
DbGroupNodes = create_orm_cls(group.DbGroupNode)
DbComment = create_orm_cls(comment.DbComment)
DbLog = create_orm_cls(log.DbLog)
DbLink = create_orm_cls(node.DbLink)

# to-do This was the minimum for creating a graph, but really all relationships should be copied
DbNode.dbcomputer = orm.relationship('DbComputer', backref='dbnodes')  # type: ignore[attr-defined]
DbGroup.dbnodes = orm.relationship(  # type: ignore[attr-defined]
    'DbNode', secondary='db_dbgroup_dbnodes', backref='dbgroups', lazy='dynamic'
)


class ZipfileBackendRepository(AbstractRepositoryBackend):
    """A read-only backend for an open zip file."""

    def __init__(self, file: ZipFile):
        self._zipfile = file

    @property
    def zipfile(self) -> ZipFile:
        if self._zipfile.fp is None:
            raise ArchiveClosedError()
        return self._zipfile

    @property
    def uuid(self) -> Optional[str]:
        return None

    @property
    def key_format(self) -> Optional[str]:
        return 'sha256'

    def initialise(self, **kwargs) -> None:
        pass

    @property
    def is_initialised(self) -> bool:
        return True

    def erase(self) -> None:
        raise ReadOnlyError()

    def _put_object_from_filelike(self, handle: BinaryIO) -> str:
        raise ReadOnlyError()

    def has_object(self, key: str) -> bool:
        try:
            self.zipfile.getinfo(f'{REPO_FOLDER}/{key}')
        except KeyError:
            return False
        return True

    def has_objects(self, keys: List[str]) -> List[bool]:
        return [self.has_object(key) for key in keys]

    def list_objects(self) -> Iterable[str]:
        for name in self.zipfile.namelist():
            if name.startswith(REPO_FOLDER + '/') and name[len(REPO_FOLDER) + 1:]:
                yield name[len(REPO_FOLDER) + 1:]

    @contextmanager
    def open(self, key: str) -> Iterator[BinaryIO]:
        try:
            handle = self.zipfile.open(f'{REPO_FOLDER}/{key}')
            yield cast(BinaryIO, handle)
        except KeyError:
            raise FileNotFoundError(f'object with key `{key}` does not exist.')
        finally:
            handle.close()

    def iter_object_streams(self, keys: List[str]) -> Iterator[Tuple[str, BinaryIO]]:
        for key in keys:
            with self.open(key) as handle:  # pylint: disable=not-context-manager
                yield key, handle

    def delete_objects(self, keys: List[str]) -> None:
        raise ReadOnlyError()

    def get_object_hash(self, key: str) -> str:
        return key

    def maintain(self, dry_run: bool = False, live: bool = True, **kwargs) -> None:
        raise NotImplementedError

    def get_info(self, statistics: bool = False, **kwargs) -> dict:
        raise NotImplementedError


class ArchiveBackendQueryBuilder(SqlaQueryBuilder):
    """Archive query builder"""

    @property
    def Node(self):
        return DbNode

    @property
    def Link(self):
        return DbLink

    @property
    def Computer(self):
        return DbComputer

    @property
    def User(self):
        return DbUser

    @property
    def Group(self):
        return DbGroup

    @property
    def AuthInfo(self):
        return DbAuthInfo

    @property
    def Comment(self):
        return DbComment

    @property
    def Log(self):
        return DbLog

    @property
    def table_groups_nodes(self):
        return DbGroupNodes.__table__  # type: ignore[attr-defined] # pylint: disable=no-member


class ArchiveReadOnlyBackend(BackendAbstract):  # pylint: disable=too-many-public-methods
    """A read-only backend for the archive."""

    @classmethod
    def version_head(cls) -> str:
        raise NotImplementedError

    @classmethod
    def version_profile(cls, profile: Profile) -> None:
        raise NotImplementedError

    @classmethod
    def migrate(cls, profile: Profile):
        raise ReadOnlyError()

    def __init__(self, profile: Profile):
        super().__init__(profile)
        self._path = Path(profile.storage_config['path'])
        if not self._path.is_file():
            raise UnreachableStorage(f'archive file `{self._path}` does not exist.')
        # lazy open the archive zipfile and extract the database file
        self._db_file: Optional[Path] = None
        self._session: Optional[orm.Session] = None
        self._zipfile: Optional[zipfile.ZipFile] = None
        self._closed = False

    def __str__(self) -> str:
        state = 'closed' if self.is_closed else 'open'
        return f'Aiida archive (read-only) [{state}] @ {self._path}'

    @property
    def is_closed(self) -> bool:
        return self._closed

    def close(self):
        """Close the backend"""
        if self._session:
            self._session.close()
        if self._db_file and self._db_file.exists():
            self._db_file.unlink()
        if self._zipfile:
            self._zipfile.close()
        self._session = None
        self._db_file = None
        self._zipfile = None
        self._closed = True

    def get_session(self) -> orm.Session:
        """Return an SQLAlchemy session."""
        if self._closed:
            raise ArchiveClosedError()
        if self._db_file is None:
            _, path = tempfile.mkstemp()
            self._db_file = Path(path)
            with self._db_file.open('wb') as handle:
                try:
                    extract_file_in_zip(self._path, DB_FILENAME, handle, search_limit=4)
                except Exception as exc:
                    raise CorruptArchive(f'database could not be read: {exc}') from exc
        if self._session is None:
            self._session = orm.Session(create_sqla_engine(self._db_file))
        return self._session

    def get_repository(self) -> ZipfileBackendRepository:
        if self._closed:
            raise ArchiveClosedError()
        if self._zipfile is None:
            self._zipfile = ZipFile(self._path, mode='r')  # pylint: disable=consider-using-with
        return ZipfileBackendRepository(self._zipfile)

    def query(self) -> ArchiveBackendQueryBuilder:
        return ArchiveBackendQueryBuilder(self)

    def get_backend_entity(self, res):  # pylint: disable=no-self-use
        """Return the backend entity that corresponds to the given Model instance."""
        klass = get_backend_entity(res)
        return klass(self, res)

    @property
    def authinfos(self):
        return create_backend_collection(authinfos.SqlaAuthInfoCollection, self, authinfos.SqlaAuthInfo, DbAuthInfo)

    @property
    def comments(self):
        return create_backend_collection(comments.SqlaCommentCollection, self, comments.SqlaComment, DbComment)

    @property
    def computers(self):
        return create_backend_collection(computers.SqlaComputerCollection, self, computers.SqlaComputer, DbComputer)

    @property
    def groups(self):
        return create_backend_collection(groups.SqlaGroupCollection, self, groups.SqlaGroup, DbGroup)

    @property
    def logs(self):
        return create_backend_collection(logs.SqlaLogCollection, self, logs.SqlaLog, DbLog)

    @property
    def nodes(self):
        return create_backend_collection(nodes.SqlaNodeCollection, self, nodes.SqlaNode, DbNode)

    @property
    def users(self):
        return create_backend_collection(users.SqlaUserCollection, self, users.SqlaUser, DbUser)

    def _clear(self, recreate_user: bool = True) -> None:
        raise ReadOnlyError()

    def transaction(self):
        raise ReadOnlyError()

    @property
    def in_transaction(self) -> bool:
        return False

    def bulk_insert(self, entity_type: EntityTypes, rows: List[dict], allow_defaults: bool = False) -> List[int]:
        raise ReadOnlyError()

    def bulk_update(self, entity_type: EntityTypes, rows: List[dict]) -> None:
        raise ReadOnlyError()

    def delete_nodes_and_connections(self, pks_to_delete: Sequence[int]):
        raise ReadOnlyError()

    def get_global_variable(self, key: str):
        raise NotImplementedError

    def set_global_variable(self, key: str, value, description: Optional[str] = None, overwrite=True) -> None:
        raise ReadOnlyError()


def create_backend_cls(base_class, model_cls):
    """Create an archive backend class for the given model class."""

    class ReadOnlyEntityBackend(base_class):  # type: ignore
        """Backend class for the read-only archive."""

        MODEL_CLASS = model_cls

        def __init__(self, _backend, model):
            """Initialise the backend entity."""
            self._backend = _backend
            self._aiida_model = ModelWrapper(model, _backend)

        @property
        def aiida_model(self) -> ModelWrapper:
            """Return an ORM model that correctly updates and flushes the data model when getting or setting a field."""
            return self._aiida_model

        @property
        def sqla_model(self):
            """Return the underlying SQLAlchemy ORM model for this entity."""
            return self.aiida_model._model  # pylint: disable=protected-access

        @classmethod
        def from_dbmodel(cls, model, _backend):
            return cls(_backend, model)

        @property
        def is_stored(self):
            return True

        def store(self):  # pylint: disable=no-self-use
            return ReadOnlyError()

    return ReadOnlyEntityBackend


def create_backend_collection(cls, _backend, entity_cls, model):
    collection = cls(_backend)
    new_cls = create_backend_cls(entity_cls, model)
    collection.ENTITY_CLASS = new_cls
    return collection


@singledispatch
def get_backend_entity(dbmodel) -> Type[entities.SqlaModelEntity]:  # pylint: disable=unused-argument
    raise TypeError(f'Cannot get backend entity for {dbmodel}')


@get_backend_entity.register(DbAuthInfo)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(authinfos.SqlaAuthInfo, dbmodel.__class__)


@get_backend_entity.register(DbComment)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(comments.SqlaComment, dbmodel.__class__)


@get_backend_entity.register(DbComputer)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(computers.SqlaComputer, dbmodel.__class__)


@get_backend_entity.register(DbGroup)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(groups.SqlaGroup, dbmodel.__class__)


@get_backend_entity.register(DbLog)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(logs.SqlaLog, dbmodel.__class__)


@get_backend_entity.register(DbNode)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(nodes.SqlaNode, dbmodel.__class__)


@get_backend_entity.register(DbUser)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(users.SqlaUser, dbmodel.__class__)
