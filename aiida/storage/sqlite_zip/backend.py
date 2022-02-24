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
from functools import singledispatch
from pathlib import Path
import tempfile
from typing import BinaryIO, Iterable, Iterator, List, Optional, Sequence, Tuple, Type, cast
import zipfile
from zipfile import ZipFile

from archive_path import extract_file_in_zip
from sqlalchemy.orm import Session

from aiida.common.exceptions import AiidaException, ClosedStorage, CorruptStorage
from aiida.manage import Profile
from aiida.orm.entities import EntityTypes
from aiida.orm.implementation import StorageBackend
from aiida.repository.backend.abstract import AbstractRepositoryBackend
from aiida.storage.psql_dos.orm import authinfos, comments, computers, entities, groups, logs, nodes, users
from aiida.storage.psql_dos.orm.querybuilder import SqlaQueryBuilder
from aiida.storage.psql_dos.orm.utils import ModelWrapper

from . import models
from .migrations.main import get_schema_version_head, validate_storage
from .utils import DB_FILENAME, REPO_FOLDER, create_sqla_engine, read_version


class SqliteZipBackend(StorageBackend):  # pylint: disable=too-many-public-methods
    """A read-only backend for a sqlite/zip format."""

    @classmethod
    def version_head(cls) -> str:
        return get_schema_version_head()

    @classmethod
    def version_profile(cls, profile: Profile) -> None:
        return read_version(profile.storage_config['path'])

    @classmethod
    def migrate(cls, profile: Profile):
        raise ReadOnlyError()

    def __init__(self, profile: Profile):
        super().__init__(profile)
        self._path = Path(profile.storage_config['path'])
        validate_storage(self._path)
        # lazy open the archive zipfile and extract the database file
        self._db_file: Optional[Path] = None
        self._session: Optional[Session] = None
        self._zipfile: Optional[zipfile.ZipFile] = None
        self._closed = False

    def __str__(self) -> str:
        state = 'closed' if self.is_closed else 'open'
        return f'SqliteZip storage (read-only) [{state}] @ {self._path}'

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

    def get_session(self) -> Session:
        """Return an SQLAlchemy session."""
        if self._closed:
            raise ClosedStorage(str(self))
        if self._db_file is None:
            _, path = tempfile.mkstemp()
            self._db_file = Path(path)
            with self._db_file.open('wb') as handle:
                try:
                    extract_file_in_zip(self._path, DB_FILENAME, handle, search_limit=4)
                except Exception as exc:
                    raise CorruptStorage(f'database could not be read: {exc}') from exc
        if self._session is None:
            self._session = Session(create_sqla_engine(self._db_file))
        return self._session

    def get_repository(self) -> 'ZipfileBackendRepository':
        if self._closed:
            raise ClosedStorage(str(self))
        if self._zipfile is None:
            self._zipfile = ZipFile(self._path, mode='r')  # pylint: disable=consider-using-with
        return ZipfileBackendRepository(self._zipfile)

    def query(self) -> 'SqliteBackendQueryBuilder':
        return SqliteBackendQueryBuilder(self)

    def get_backend_entity(self, res):  # pylint: disable=no-self-use
        """Return the backend entity that corresponds to the given Model instance."""
        klass = get_backend_entity(res)
        return klass(self, res)

    @property
    def authinfos(self):
        return create_backend_collection(
            authinfos.SqlaAuthInfoCollection, self, authinfos.SqlaAuthInfo, models.DbAuthInfo
        )

    @property
    def comments(self):
        return create_backend_collection(comments.SqlaCommentCollection, self, comments.SqlaComment, models.DbComment)

    @property
    def computers(self):
        return create_backend_collection(
            computers.SqlaComputerCollection, self, computers.SqlaComputer, models.DbComputer
        )

    @property
    def groups(self):
        return create_backend_collection(groups.SqlaGroupCollection, self, groups.SqlaGroup, models.DbGroup)

    @property
    def logs(self):
        return create_backend_collection(logs.SqlaLogCollection, self, logs.SqlaLog, models.DbLog)

    @property
    def nodes(self):
        return create_backend_collection(nodes.SqlaNodeCollection, self, nodes.SqlaNode, models.DbNode)

    @property
    def users(self):
        return create_backend_collection(users.SqlaUserCollection, self, users.SqlaUser, models.DbUser)

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

    def maintain(self, dry_run: bool = False, live: bool = True, **kwargs) -> None:
        raise NotImplementedError

    def get_info(self, statistics: bool = False, **kwargs) -> dict:
        raise NotImplementedError


class ReadOnlyError(AiidaException):
    """Raised when a write operation is called on a read-only archive."""

    def __init__(self, msg='sqlite_zip storage is read-only'):  # pylint: disable=useless-super-delegation
        super().__init__(msg)


class ZipfileBackendRepository(AbstractRepositoryBackend):
    """A read-only backend for an open zip file."""

    def __init__(self, file: ZipFile):
        self._zipfile = file

    @property
    def zipfile(self) -> ZipFile:
        if self._zipfile.fp is None:
            raise ClosedStorage(f'zipfile closed: {self._zipfile}')
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
        return {'objects': {'count': len(list(self.list_objects()))}}


class SqliteBackendQueryBuilder(SqlaQueryBuilder):
    """Archive query builder"""

    @property
    def Node(self):
        return models.DbNode

    @property
    def Link(self):
        return models.DbLink

    @property
    def Computer(self):
        return models.DbComputer

    @property
    def User(self):
        return models.DbUser

    @property
    def Group(self):
        return models.DbGroup

    @property
    def AuthInfo(self):
        return models.DbAuthInfo

    @property
    def Comment(self):
        return models.DbComment

    @property
    def Log(self):
        return models.DbLog

    @property
    def table_groups_nodes(self):
        return models.DbGroupNodes.__table__  # type: ignore[attr-defined] # pylint: disable=no-member

    def maintain(self, full: bool = False, dry_run: bool = False, **kwargs) -> None:
        raise NotImplementedError

    def get_info(self, statistics: bool = False) -> dict:
        results = super().get_info(statistics=statistics)
        results['repository'] = self.get_repository().get_info(statistics)
        return results


def create_backend_cls(base_class, model_cls):
    """Create an archive backend class for the given model class."""

    class ReadOnlyEntityBackend(base_class):  # type: ignore
        """Backend class for the read-only archive."""

        MODEL_CLASS = model_cls

        def __init__(self, _backend, model):
            """Initialise the backend entity."""
            self._backend = _backend
            self._model = ModelWrapper(model, _backend)

        @property
        def model(self) -> ModelWrapper:
            """Return an ORM model that correctly updates and flushes the data model when getting or setting a field."""
            return self._model

        @property
        def bare_model(self):
            """Return the underlying SQLAlchemy ORM model for this entity."""
            return self.model._model  # pylint: disable=protected-access

        @classmethod
        def from_dbmodel(cls, model, _backend):
            return cls(_backend, model)

        @property
        def is_stored(self):
            return True

        def store(self):  # pylint: disable=no-self-use
            raise ReadOnlyError()

    return ReadOnlyEntityBackend


def create_backend_collection(cls, _backend, entity_cls, model):
    collection = cls(_backend)
    new_cls = create_backend_cls(entity_cls, model)
    collection.ENTITY_CLASS = new_cls
    return collection


@singledispatch
def get_backend_entity(dbmodel) -> Type[entities.SqlaModelEntity]:  # pylint: disable=unused-argument
    raise TypeError(f'Cannot get backend entity for {dbmodel}')


@get_backend_entity.register(models.DbAuthInfo)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(authinfos.SqlaAuthInfo, dbmodel.__class__)


@get_backend_entity.register(models.DbComment)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(comments.SqlaComment, dbmodel.__class__)


@get_backend_entity.register(models.DbComputer)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(computers.SqlaComputer, dbmodel.__class__)


@get_backend_entity.register(models.DbGroup)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(groups.SqlaGroup, dbmodel.__class__)


@get_backend_entity.register(models.DbLog)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(logs.SqlaLog, dbmodel.__class__)


@get_backend_entity.register(models.DbNode)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(nodes.SqlaNode, dbmodel.__class__)


@get_backend_entity.register(models.DbUser)  # type: ignore[call-overload]
def _(dbmodel):
    return create_backend_cls(users.SqlaUser, dbmodel.__class__)
