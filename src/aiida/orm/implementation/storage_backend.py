###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic backend related objects"""

from __future__ import annotations

import abc
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ContextManager, List, Optional, TypeVar, Union

if TYPE_CHECKING:
    from aiida.manage.configuration.profile import Profile
    from aiida.orm.autogroup import AutogroupManager
    from aiida.orm.entities import EntityTypes
    from aiida.orm.implementation import (
        BackendAuthInfoCollection,
        BackendCommentCollection,
        BackendComputerCollection,
        BackendGroupCollection,
        BackendLogCollection,
        BackendNodeCollection,
        BackendQueryBuilder,
        BackendUserCollection,
    )
    from aiida.orm.users import User
    from aiida.repository.backend.abstract import AbstractRepositoryBackend

__all__ = ('StorageBackend',)

TransactionType = TypeVar('TransactionType')


class StorageBackend(abc.ABC):
    """Abstraction for a backend to read/write persistent data for a profile's provenance graph.

    AiiDA splits data storage into two sources:

    - Searchable data, which is stored in the database and can be queried using the QueryBuilder
    - Non-searchable (binary) data, which is stored in the repository and can be loaded using the RepositoryBackend

    The two sources are inter-linked by the ``Node.base.repository.metadata``.
    Once stored, the leaf values of this dictionary must be valid pointers to object keys in the repository.

    For a completely new storage, the ``initialise`` method should be called first. This will automatically initialise
    the repository and the database with the current schema. The class methods,`version_profile` and `migrate` should be
    able to be called for existing storage, at any supported schema version. But an instance of this class should be
    created only for the latest schema version.
    """

    read_only = False

    @classmethod
    @abc.abstractmethod
    def version_head(cls) -> str:
        """Return the head schema version of this storage backend type."""

    @classmethod
    @abc.abstractmethod
    def version_profile(cls, profile: 'Profile') -> Optional[str]:
        """Return the schema version of the given profile's storage, or None for empty/uninitialised storage.

        :raises: `~aiida.common.exceptions.UnreachableStorage` if the storage cannot be accessed
        """

    @classmethod
    @abc.abstractmethod
    def initialise(cls, profile: 'Profile', reset: bool = False) -> bool:
        """Initialise the storage backend.

        This is typically used once when a new storage backed is created. If this method returns without exceptions the
        storage backend is ready for use. If the backend already seems initialised, this method is a no-op.

        :param reset: If ``true``, destroy the backend if it already exists including all of its data before recreating
            and initialising it. This is useful for example for test profiles that need to be reset before or after
            tests having run.
        :returns: ``True`` if the storage was initialised by the function call, ``False`` if it was already initialised.
        """

    @classmethod
    @abc.abstractmethod
    def migrate(cls, profile: 'Profile') -> None:
        """Migrate the storage of a profile to the latest schema version.

        If the schema version is already the latest version, this method does nothing. If the storage is uninitialised,
        this method will raise an exception.

        :raises: :class`~aiida.common.exceptions.UnreachableStorage` if the storage cannot be accessed.
        :raises: :class:`~aiida.common.exceptions.StorageMigrationError` if the storage is not initialised.
        """

    @abc.abstractmethod
    def __init__(self, profile: 'Profile') -> None:
        """Initialize the backend, for this profile.

        :raises: `~aiida.common.exceptions.UnreachableStorage` if the storage cannot be accessed
        :raises: `~aiida.common.exceptions.IncompatibleStorageSchema`
            if the profile's storage schema is not at the latest version (and thus should be migrated)
        :raises: :raises: :class:`aiida.common.exceptions.CorruptStorage` if the storage is internally inconsistent
        """
        from aiida.orm.autogroup import AutogroupManager

        self._profile = profile
        self._default_user: Optional['User'] = None
        self._autogroup = AutogroupManager(self)

    @abc.abstractmethod
    def __str__(self) -> str:
        """Return a string showing connection details for this instance."""

    @property
    def profile(self) -> 'Profile':
        """Return the profile for this backend."""
        return self._profile

    @property
    def autogroup(self) -> 'AutogroupManager':
        """Return the autogroup manager for this backend."""
        return self._autogroup

    def version(self) -> str:
        """Return the schema version of the profile's storage."""
        version = self.version_profile(self.profile)
        assert version is not None
        return version

    @abc.abstractmethod
    def close(self):
        """Close the storage access."""

    @property
    @abc.abstractmethod
    def is_closed(self) -> bool:
        """Return whether the storage is closed."""

    @abc.abstractmethod
    def _clear(self) -> None:
        """Clear the storage, removing all data.

        .. warning:: This is a destructive operation, and should only be used for testing purposes.
        """
        from aiida.orm.autogroup import AutogroupManager

        self.reset_default_user()
        self._autogroup = AutogroupManager(self)

    def reset_default_user(self) -> None:
        """Reset the default user.

        This should be done when the default user of the storage backend is changed on the corresponding profile because
        the old default user is cached on this instance.
        """
        self._default_user = None

    @property
    @abc.abstractmethod
    def authinfos(self) -> 'BackendAuthInfoCollection':
        """Return the collection of authorisation information objects"""

    @property
    @abc.abstractmethod
    def comments(self) -> 'BackendCommentCollection':
        """Return the collection of comments"""

    @property
    @abc.abstractmethod
    def computers(self) -> 'BackendComputerCollection':
        """Return the collection of computers"""

    @property
    @abc.abstractmethod
    def groups(self) -> 'BackendGroupCollection':
        """Return the collection of groups"""

    @property
    @abc.abstractmethod
    def logs(self) -> 'BackendLogCollection':
        """Return the collection of logs"""

    @property
    @abc.abstractmethod
    def nodes(self) -> 'BackendNodeCollection':
        """Return the collection of nodes"""

    @property
    @abc.abstractmethod
    def users(self) -> 'BackendUserCollection':
        """Return the collection of users"""

    @property
    def default_user(self) -> Optional['User']:
        """Return the default user for the profile, if it has been created.

        This is cached, since it is a frequently used operation, for creating other entities.
        """
        from aiida.orm import QueryBuilder, User

        if self._default_user is None and self.profile.default_user_email:
            query = QueryBuilder(self).append(User, filters={'email': self.profile.default_user_email})
            self._default_user = query.first(flat=True)
        return self._default_user

    @abc.abstractmethod
    def query(self) -> 'BackendQueryBuilder':
        """Return an instance of a query builder implementation for this backend"""

    @abc.abstractmethod
    def transaction(self) -> ContextManager[Any]:
        """Get a context manager that can be used as a transaction context for a series of backend operations.
        If there is an exception within the context then the changes will be rolled back and the state will
        be as before entering.  Transactions can be nested.

        :return: a context manager to group database operations
        """

    @property
    @abc.abstractmethod
    def in_transaction(self) -> bool:
        """Return whether a transaction is currently active."""

    @abc.abstractmethod
    def bulk_insert(self, entity_type: 'EntityTypes', rows: List[dict], allow_defaults: bool = False) -> List[int]:
        """Insert a list of entities into the database, directly into a backend transaction.

        :param entity_type: The type of the entity
        :param data: A list of dictionaries, containing all fields of the backend model,
            except the `id` field (a.k.a primary key), which will be generated dynamically
        :param allow_defaults: If ``False``, assert that each row contains all fields (except primary key(s)),
            otherwise, allow default values for missing fields.

        :raises: ``IntegrityError`` if the keys in a row are not a subset of the columns in the table

        :returns: The list of generated primary keys for the entities
        """

    @abc.abstractmethod
    def bulk_update(self, entity_type: 'EntityTypes', rows: List[dict]) -> None:
        """Update a list of entities in the database, directly with a backend transaction.

        :param entity_type: The type of the entity
        :param data: A list of dictionaries, containing fields of the backend model to update,
            and the `id` field (a.k.a primary key)

        :raises: ``IntegrityError`` if the keys in a row are not a subset of the columns in the table
        """

    def delete(self) -> None:
        """Delete the storage and all the data."""
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_nodes_and_connections(self, pks_to_delete: Iterable[int]) -> None:
        """Delete all nodes corresponding to pks in the input and any links to/from them.

        This method is intended to be used within a transaction context.

        :param pks_to_delete: an iterable of node pks to delete

        :raises: ``AssertionError`` if a transaction is not active
        """

    @abc.abstractmethod
    def get_repository(self) -> 'AbstractRepositoryBackend':
        """Return the object repository configured for this backend."""

    @abc.abstractmethod
    def set_global_variable(
        self, key: str, value: Union[None, str, int, float], description: Optional[str] = None, overwrite=True
    ) -> None:
        """Set a global variable in the storage.

        :param key: the key of the setting
        :param value: the value of the setting
        :param description: the description of the setting (optional)
        :param overwrite: if True, overwrite the setting if it already exists

        :raises: `ValueError` if the key already exists and `overwrite` is False
        """

    @abc.abstractmethod
    def get_global_variable(self, key: str) -> Union[None, str, int, float]:
        """Return a global variable from the storage.

        :param key: the key of the setting

        :raises: `KeyError` if the setting does not exist
        """

    @abc.abstractmethod
    def maintain(self, full: bool = False, dry_run: bool = False, **kwargs) -> None:
        """Perform maintenance tasks on the storage.

        If `full == True`, then this method may attempt to block the profile associated with the
        storage to guarantee the safety of its procedures. This will not only prevent any other
        subsequent process from accessing that profile, but will also first check if there is
        already any process using it and raise if that is the case. The user will have to manually
        stop any processes that is currently accessing the profile themselves or wait for it to
        finish on its own.

        :param full: flag to perform operations that require to stop using the profile to be maintained.
        :param dry_run: flag to only print the actions that would be taken without actually executing them.
        """

    def _backup(
        self,
        dest: str,
        keep: Optional[int] = None,
    ):
        raise NotImplementedError

    def _write_backup_config(self, backup_manager):
        import pathlib
        import tempfile

        from aiida.common import exceptions
        from aiida.common.log import override_log_level
        from aiida.manage.configuration import get_config
        from aiida.manage.configuration.config import Config
        from aiida.manage.configuration.settings import DEFAULT_CONFIG_FILE_NAME

        try:
            config = get_config()
            profile = config.get_profile(self.profile.name)  # Get the profile being backed up
            with tempfile.TemporaryDirectory() as tmpdir:
                filepath_config = pathlib.Path(tmpdir) / DEFAULT_CONFIG_FILE_NAME
                backup_config = Config(str(filepath_config), {})  # Create empty config at temporary file location
                backup_config.add_profile(profile)  # Add the profile being backed up
                backup_config.store()  # Write the contents to disk

                # Temporarily disable all logging because the verbose rsync output just for copying the config file
                # is a bit much.
                with override_log_level():
                    backup_manager.call_rsync(filepath_config, backup_manager.path / DEFAULT_CONFIG_FILE_NAME)
        except (exceptions.MissingConfigurationError, exceptions.ConfigurationError) as exc:
            raise exceptions.StorageBackupError('AiiDA config.json not found!') from exc

    def _validate_or_init_backup_folder(self, dest, keep):
        import json
        import tempfile

        from disk_objectstore import backup_utils

        from aiida.common import exceptions
        from aiida.manage.configuration.config import Config
        from aiida.manage.configuration.settings import DEFAULT_CONFIG_FILE_NAME
        from aiida.storage.log import STORAGE_LOGGER

        try:
            # this creates the dest folder if it doesn't exist
            backup_manager = backup_utils.BackupManager(dest, keep=keep)
            backup_config_path = backup_manager.path / DEFAULT_CONFIG_FILE_NAME

            if backup_manager.check_path_exists(backup_config_path):
                success, stdout = backup_manager.run_cmd(['cat', str(backup_config_path)])
                if not success:
                    raise exceptions.StorageBackupError(f"Couldn't read {backup_config_path!s}.")
                try:
                    backup_config_existing = json.loads(stdout)
                except json.decoder.JSONDecodeError as exc:
                    raise exceptions.StorageBackupError(f'JSON parsing failed for {backup_config_path!s}: {exc.msg}')

                # create a temporary config file to access the profile info
                with tempfile.NamedTemporaryFile() as temp_file:
                    backup_config = Config(temp_file.name, backup_config_existing, validate=False)
                    if len(backup_config.profiles) != 1:
                        raise exceptions.StorageBackupError(f"{backup_config_path!s} doesn't contain exactly 1 profile")

                    if (
                        backup_config.profiles[0].uuid != self.profile.uuid
                        or backup_config.profiles[0].storage_backend != self.profile.storage_backend
                    ):
                        raise exceptions.StorageBackupError(
                            'The chosen destination contains backups of a different profile! Aborting!'
                        )
            else:
                STORAGE_LOGGER.warning('Initializing a new backup folder.')
                # make sure the folder is empty
                success, stdout = backup_manager.run_cmd(['ls', '-A', str(backup_manager.path)])
                if not success:
                    raise exceptions.StorageBackupError(f"Couldn't read {backup_manager.path!s}.")
                if stdout:
                    raise exceptions.StorageBackupError("Can't initialize the backup folder, destination is not empty.")

                self._write_backup_config(backup_manager)

        except backup_utils.BackupError as exc:
            raise exceptions.StorageBackupError(*exc.args) from exc

        return backup_manager

    def backup(
        self,
        dest: str,
        keep: Optional[int] = None,
    ):
        """Create a backup of the storage contents.

        :param dest: The path to the destination folder.
        :param keep: The number of backups to keep in the target destination, if the backend supports it.
        :raises ValueError: If the input parameters are invalid.
        :raises StorageBackupError: If an error occurred during the backup procedure.
        :raises NotImplementedError: If the storage backend doesn't implement a backup procedure.
        """
        from aiida.common.exceptions import LockedProfileError, StorageBackupError
        from aiida.manage.configuration.settings import DEFAULT_CONFIG_FILE_NAME
        from aiida.manage.profile_access import ProfileAccessManager
        from aiida.storage.log import STORAGE_LOGGER

        # check that the AiiDA profile is not locked and request access for the duration of this backup process
        # (locked means that possibly a maintenance operation is running that could interfere with the backup)
        try:
            ProfileAccessManager(self._profile).request_access()
        except LockedProfileError as exc:
            raise StorageBackupError(f'{self._profile} is locked!') from exc

        backup_manager = self._validate_or_init_backup_folder(dest, keep)

        try:
            self._backup(dest, keep)
        except NotImplementedError:
            success, stdout = backup_manager.run_cmd(['ls', '-A', str(backup_manager.path)])

            if not success:
                STORAGE_LOGGER.warning(f'Failed to determine contents of destination folder `{dest}`: not deleting it.')
                raise

            # If the backup directory was just initialized for the first time, it should only contain the configuration
            # file and nothing else. If anything else is found, do not delete the directory for safety reasons.
            if stdout.strip() != DEFAULT_CONFIG_FILE_NAME:
                STORAGE_LOGGER.warning(f'The destination folder `{dest}` is not empty: not deleting it.')
                raise

            backup_manager.run_cmd(['rm', '-rf', str(backup_manager.path)])
            raise

        STORAGE_LOGGER.report(f'Overwriting the `{DEFAULT_CONFIG_FILE_NAME} file.')
        self._write_backup_config(backup_manager)

    def get_info(self, detailed: bool = False) -> dict:
        """Return general information on the storage.

        :param detailed: flag to request more detailed information about the content of the storage.
        :returns: a nested dict with the relevant information.
        """
        return {'entities': self.get_orm_entities(detailed=detailed)}

    def get_orm_entities(self, detailed: bool = False) -> dict:
        """Return a mapping with an overview of the storage contents regarding ORM entities.

        :param detailed: flag to request more detailed information about the content of the storage.
        :returns: a nested dict with the relevant information.
        """
        from aiida.orm import Comment, Computer, Group, Log, Node, QueryBuilder, User

        data: dict[str, Any] = {}

        query_user = QueryBuilder(self).append(User, project=['email'])
        data['Users'] = {'count': query_user.count()}
        if detailed:
            data['Users']['emails'] = sorted({email for (email,) in query_user.iterall() if email is not None})

        query_comp = QueryBuilder(self).append(Computer, project=['label'])
        data['Computers'] = {'count': query_comp.count()}
        if detailed:
            data['Computers']['labels'] = sorted({comp for (comp,) in query_comp.iterall() if comp is not None})

        count = QueryBuilder(self).append(Node).count()
        data['Nodes'] = {'count': count}
        if detailed:
            node_types = sorted(
                {typ for (typ,) in QueryBuilder(self).append(Node, project=['node_type']).iterall() if typ is not None}
            )
            data['Nodes']['node_types'] = node_types
            process_types = sorted(
                {
                    typ
                    for (typ,) in QueryBuilder(self).append(Node, project=['process_type']).iterall()
                    if typ is not None
                }
            )
            data['Nodes']['process_types'] = [p for p in process_types if p]

        query_group = QueryBuilder(self).append(Group, project=['type_string'])
        data['Groups'] = {'count': query_group.count()}
        if detailed:
            data['Groups']['type_strings'] = sorted({typ for (typ,) in query_group.iterall() if typ is not None})

        count = QueryBuilder(self).append(Comment).count()
        data['Comments'] = {'count': count}

        count = QueryBuilder(self).append(Log).count()
        data['Logs'] = {'count': count}

        count = QueryBuilder(self).append(entity_type='link').count()
        data['Links'] = {'count': count}

        return data
