###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of the ``SqliteTempBackend`` backend."""

from __future__ import annotations

import functools
import hashlib
import os
import shutil
from collections.abc import Iterable, Iterator
from contextlib import contextmanager, nullcontext
from pathlib import Path
from tempfile import mkdtemp
from typing import Any, BinaryIO

from pydantic import BaseModel, Field
from sqlalchemy import column, insert, update
from sqlalchemy.orm import Session

from aiida.common.exceptions import ClosedStorage, IntegrityError
from aiida.manage.configuration import Profile
from aiida.orm.entities import EntityTypes
from aiida.orm.implementation import BackendEntity, StorageBackend
from aiida.repository.backend.sandbox import SandboxRepositoryBackend
from aiida.storage.sqlite_zip import models, orm
from aiida.storage.sqlite_zip.migrator import get_schema_version_head
from aiida.storage.sqlite_zip.utils import create_sqla_engine

__all__ = ('SqliteTempBackend',)


class SqliteTempBackend(StorageBackend):
    """A temporary backend, using an in-memory sqlite database.

    This backend is intended for testing and demonstration purposes.
    Whenever it is instantiated, it creates a fresh storage backend,
    and destroys it when it is garbage collected.
    """

    class Model(BaseModel, defer_build=True):
        filepath: str = Field(
            title='Temporary directory',
            description='Temporary directory in which to store data for this backend.',
            default_factory=mkdtemp,
        )

    cli_exposed = False
    """Ensure this plugin is not exposed in ``verdi profile setup``."""

    @staticmethod
    def create_profile(
        name: str = 'temp',
        default_user_email='user@email.com',
        options: dict | None = None,
        debug: bool = False,
        filepath: str | Path | None = None,
    ) -> Profile:
        """Create a new profile instance for this backend, from the path to the zip file."""
        return Profile(
            name,
            {
                'default_user_email': default_user_email,
                'storage': {
                    'backend': 'core.sqlite_temp',
                    'config': {
                        'filepath': filepath,
                        'debug': debug,
                    },
                },
                'process_control': {'backend': None, 'config': {}},
                'options': options or {},
            },
        )

    @classmethod
    def version_head(cls) -> str:
        return get_schema_version_head()

    @classmethod
    def version_profile(cls, profile: Profile) -> str | None:
        return get_schema_version_head()

    @classmethod
    def initialise(cls, profile: 'Profile', reset: bool = False) -> bool:
        return False

    @classmethod
    def migrate(cls, profile: Profile):
        pass

    def __init__(self, profile: Profile):
        super().__init__(profile)
        self._session: Session | None = None
        self._repo: SandboxShaRepositoryBackend = SandboxShaRepositoryBackend(profile.storage_config['filepath'])
        self._globals: dict[str, tuple[Any, str | None]] = {}
        self._closed = False
        self.get_session()  # load the database on initialization

    def __str__(self) -> str:
        state = 'closed' if self.is_closed else 'open'
        return f'SqliteTemp storage [{state}], sandbox: {self._repo}'

    @property
    def is_closed(self) -> bool:
        return self._closed

    def close(self):
        if self._session:
            self._session.close()
        if self._repo:
            self._repo.erase()
        self._session = None
        self._repo = None
        self._globals = {}
        self._closed = True

    def get_global_variable(self, key: str):
        return self._globals[key][0]

    def set_global_variable(self, key: str, value, description: str | None = None, overwrite=True) -> None:
        if not overwrite and key in self._globals:
            raise ValueError(f'global variable {key} already exists')
        self._globals[key] = (value, description)

    def get_session(self) -> Session:
        """Return an SQLAlchemy session."""
        if self._closed:
            raise ClosedStorage(str(self))
        if self._session is None:
            engine = create_sqla_engine(':memory:', echo=self.profile.storage_config.get('debug', False))
            models.SqliteBase.metadata.create_all(engine)
            self._session = Session(engine, future=True)
            self._session.add(models.DbUser(email=self.profile.default_user_email or 'user@email.com'))
            self._session.commit()
        return self._session

    def get_repository(self) -> SandboxShaRepositoryBackend:
        if self._closed:
            raise ClosedStorage(str(self))
        return self._repo

    @property
    def in_transaction(self) -> bool:
        return self.get_session().in_nested_transaction()

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

    def _clear(self) -> None:
        raise NotImplementedError

    def maintain(self, dry_run: bool = False, live: bool = True, **kwargs) -> None:
        pass

    def query(self) -> orm.SqliteQueryBuilder:
        return orm.SqliteQueryBuilder(self)

    def get_backend_entity(self, model) -> BackendEntity:
        """Return the backend entity that corresponds to the given Model instance."""
        return orm.get_backend_entity(model, self)

    @functools.cached_property
    def authinfos(self):
        return orm.SqliteAuthInfoCollection(self)

    @functools.cached_property
    def comments(self):
        return orm.SqliteCommentCollection(self)

    @functools.cached_property
    def computers(self):
        return orm.SqliteComputerCollection(self)

    @functools.cached_property
    def groups(self):
        return orm.SqliteGroupCollection(self)

    @functools.cached_property
    def logs(self):
        return orm.SqliteLogCollection(self)

    @functools.cached_property
    def nodes(self):
        return orm.SqliteNodeCollection(self)

    @functools.cached_property
    def users(self):
        return orm.SqliteUserCollection(self)

    def get_info(self, detailed: bool = False) -> dict:
        results = super().get_info(detailed=detailed)
        # results['repository'] = self.get_repository().get_info(detailed)
        return results

    @staticmethod
    @functools.lru_cache(maxsize=18)
    def _get_mapper_from_entity(entity_type: EntityTypes, with_pk: bool):
        """Return the Sqlalchemy mapper and fields corresponding to the given entity.

        :param with_pk: if True, the fields returned will include the primary key
        """
        from sqlalchemy import inspect

        from aiida.storage.sqlite_zip.models import (
            DbAuthInfo,
            DbComment,
            DbComputer,
            DbGroup,
            DbGroupNodes,
            DbLink,
            DbLog,
            DbNode,
            DbUser,
        )

        model = {
            EntityTypes.AUTHINFO: DbAuthInfo,
            EntityTypes.COMMENT: DbComment,
            EntityTypes.COMPUTER: DbComputer,
            EntityTypes.GROUP: DbGroup,
            EntityTypes.LOG: DbLog,
            EntityTypes.NODE: DbNode,
            EntityTypes.USER: DbUser,
            EntityTypes.LINK: DbLink,
            EntityTypes.GROUP_NODE: DbGroupNodes,
        }[entity_type]
        mapper = inspect(model).mapper
        keys = {key for key, col in mapper.c.items() if with_pk or col not in mapper.primary_key}
        return mapper, keys

    def bulk_insert(self, entity_type: EntityTypes, rows: list[dict], allow_defaults: bool = False) -> list[int]:
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
        session = self.get_session()
        with nullcontext() if self.in_transaction else self.transaction():
            result = session.execute(insert(mapper).returning(mapper, column('id')), rows).fetchall()
        return [row.id for row in result]

    def bulk_update(self, entity_type: EntityTypes, rows: list[dict]) -> None:
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

    def delete(self) -> None:
        """Delete the storage and all the data."""
        self._repo.erase()

    def delete_nodes_and_connections(self, pks_to_delete: Iterable[int]) -> None:
        raise NotImplementedError


class SandboxShaRepositoryBackend(SandboxRepositoryBackend):
    """A sandbox repository backend that uses the sha256 of the file as the key.

    This allows for compatibility with the archive format (i.e. `SqliteZipBackend`).
    Which allows for temporary profiles to be exported and imported.
    """

    @property
    def key_format(self) -> str | None:
        return 'sha256'

    def get_object_hash(self, key: str) -> str:
        return key

    def _put_object_from_filelike(self, handle: BinaryIO) -> str:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
        # we first compute the hash of the file contents
        hsh = hashlib.sha256()
        position = handle.tell()
        while True:
            buf = handle.read(1024 * 1024)
            if not buf:
                break
            hsh.update(buf)
        key = hsh.hexdigest()

        filepath = os.path.join(self.sandbox.abspath, key)
        if not os.path.exists(filepath):
            # if a file with this hash does not already exist
            # then we reset the file pointer and copy the contents
            handle.seek(position)
            with open(filepath, 'wb') as target:
                shutil.copyfileobj(handle, target)

        return key

    def get_info(self, detailed: bool = False, **kwargs) -> dict:
        return {'objects': {'count': len(list(self.list_objects()))}}

    def maintain(self, dry_run: bool = False, live: bool = True, **kwargs) -> None:
        pass
