# -*- coding: utf-8 -*-
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

from contextlib import contextmanager
from functools import cached_property
from typing import Any, Iterator, Sequence

from sqlalchemy.orm import Session

from aiida.common.exceptions import ClosedStorage
from aiida.manage import Profile, get_config_option
from aiida.orm.entities import EntityTypes
from aiida.orm.implementation import BackendEntity, StorageBackend
from aiida.repository.backend.sandbox import SandboxRepositoryBackend
from aiida.storage.sqlite_zip import models, orm
from aiida.storage.sqlite_zip.migrator import get_schema_version_head
from aiida.storage.sqlite_zip.utils import create_sqla_engine

__all__ = ('SqliteTempBackend',)


class SqliteTempBackend(StorageBackend):  # pylint: disable=too-many-public-methods
    """A temporary backend, using an in-memory sqlite database.

    This backend is intended for testing and demonstration purposes.
    Whenever it is instantiated, it creates a fresh storage backend,
    and destroys it when it is garbage collected.
    """
    _read_only = False

    @staticmethod
    def create_profile(
        name: str = 'temp',
        default_user_email='user@email.com',
        options: dict | None = None,
        debug: bool = False
    ) -> Profile:
        """Create a new profile instance for this backend, from the path to the zip file."""
        return Profile(
            name, {
                'default_user_email': default_user_email,
                'storage': {
                    'backend': 'core.sqlite_temp',
                    'config': {
                        'debug': debug,
                    }
                },
                'process_control': {
                    'backend': 'null',
                    'config': {}
                },
                'options': options or {},
            }
        )

    @classmethod
    def version_head(cls) -> str:
        return get_schema_version_head()

    @classmethod
    def version_profile(cls, profile: Profile) -> str | None:  # pylint: disable=unused-argument
        return get_schema_version_head()

    @classmethod
    def initialise(cls, profile: 'Profile', reset: bool = False) -> bool:  # pylint: disable=unused-argument
        return False

    @classmethod
    def migrate(cls, profile: Profile):
        pass

    def __init__(self, profile: Profile):
        super().__init__(profile)
        self._session: Session | None = None
        self._repo: SandboxRepositoryBackend | None = None
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

    def set_global_variable(self, key: str, value, description: str | None = None, overwrite=True) -> None:  # pylint: disable=unused-argument
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

    def get_repository(self) -> SandboxRepositoryBackend:
        if self._closed:
            raise ClosedStorage(str(self))
        if self._repo is None:
            # to-do this does not seem to be removing the folder on garbage collection?
            self._repo = SandboxRepositoryBackend(filepath=get_config_option('storage.sandbox') or None)
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

    @cached_property
    def authinfos(self):
        return orm.SqliteAuthInfoCollection(self)

    @cached_property
    def comments(self):
        return orm.SqliteCommentCollection(self)

    @cached_property
    def computers(self):
        return orm.SqliteComputerCollection(self)

    @cached_property
    def groups(self):
        return orm.SqliteGroupCollection(self)

    @cached_property
    def logs(self):
        return orm.SqliteLogCollection(self)

    @cached_property
    def nodes(self):
        return orm.SqliteNodeCollection(self)

    @cached_property
    def users(self):
        return orm.SqliteUserCollection(self)

    def get_info(self, detailed: bool = False) -> dict:
        results = super().get_info(detailed=detailed)
        # results['repository'] = self.get_repository().get_info(detailed)
        return results

    def bulk_insert(self, entity_type: EntityTypes, rows: list[dict], allow_defaults: bool = False) -> list[int]:
        raise NotImplementedError

    def bulk_update(self, entity_type: EntityTypes, rows: list[dict]) -> None:
        raise NotImplementedError

    def delete_nodes_and_connections(self, pks_to_delete: Sequence[int]):
        raise NotImplementedError
