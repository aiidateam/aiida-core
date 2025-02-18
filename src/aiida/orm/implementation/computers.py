###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend specific computer objects and methods"""

from __future__ import annotations

import abc
import logging
from typing import Any, Dict, Protocol

from .entities import BackendCollection, BackendEntity

__all__ = ('BackendComputer', 'BackendComputerCollection')


class HasUUID(Protocol):
    @property
    def uuid(self) -> str:
        """A required UUID property."""
        ...


class BackendComputer(BackendEntity):
    """Backend implementation for the `Computer` ORM class.

    A computer is a resource that can be used to run calculations:
    It has an associated transport_type, which points to a plugin for connecting to the resource and passing data,
    and a scheduler_type, which points to a plugin for scheduling calculations.
    """

    _logger = logging.getLogger(__name__)

    @property
    @abc.abstractmethod
    def uuid(self) -> str:
        """Return the UUID of the computer."""

    @property
    @abc.abstractmethod
    def label(self) -> str:
        """Return the (unique) label of the computer."""

    @abc.abstractmethod
    def set_label(self, val: str):
        """Set the (unique) label of the computer."""

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Return the description of the computer."""

    @abc.abstractmethod
    def set_description(self, val: str):
        """Set the description of the computer."""

    @property
    @abc.abstractmethod
    def hostname(self) -> str:
        """Return the hostname of the computer (used to associate the connected device)."""

    @abc.abstractmethod
    def set_hostname(self, val: str) -> None:
        """Set the hostname of this computer
        :param val: The new hostname
        """

    @abc.abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return the metadata for the computer."""

    @abc.abstractmethod
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set the metadata for the computer."""

    @abc.abstractmethod
    def get_scheduler_type(self) -> str:
        """Return the scheduler plugin type."""

    @abc.abstractmethod
    def set_scheduler_type(self, scheduler_type: str) -> None:
        """Set the scheduler plugin type."""

    @abc.abstractmethod
    def get_transport_type(self) -> str:
        """Return the transport plugin type."""

    @abc.abstractmethod
    def set_transport_type(self, transport_type: str) -> None:
        """Set the transport plugin type."""

    @abc.abstractmethod
    def copy(self) -> 'BackendComputer':
        """Create an un-stored clone of an already stored `Computer`.

        :raises: ``InvalidOperation`` if the computer is not stored.
        """

    class ComputerPasswordManager:
        # To support both BackendComputer, DbComputer we only require uuid as typehint
        # During the deletion of the computer from the database, the password is also deleted
        # There we need to support a construction passing a DbComputer.
        def __init__(self, computer: HasUUID):
            self._computer = computer

        def get(self) -> str | None:
            """Retrieves the password associated with this computer from system's secure storage

            :raises RuntimeError: If the keychain is not accessible.
            """
            from keyringrs import Entry

            try:
                return Entry('aiida', f'{self._computer.uuid}').get_password()
            except RuntimeError as exc:
                # error when no password for entry is available
                if str(exc) == 'No matching entry found in secure storage':
                    return None
                raise

        def set(self, password: str) -> None:
            """Sets the entry with the uuid of the computer to system's secure storage with the `password`.

            :raises RuntimeError: If the keychain is not accessible.
            """
            from keyringrs import Entry

            Entry('aiida', f'{self._computer.uuid}').set_password(password)

        def delete(self) -> None:
            """Deletes the password associated with this computer from system's secure storage if available.

            :raises RuntimeError: If the keychain is not accessible.
            """
            from keyringrs import Entry

            try:
                Entry('aiida', f'{self._computer.uuid}').delete_credential()
            except RuntimeError as exc:
                # error when no password for entry is available
                if str(exc) == 'No matching entry found in secure storage':
                    return None
                raise

        def get_cmd_stdout_password(self) -> str:
            """Returns the command line command to retrieve the password to stdout.

            This is needed for the gotocomputer commands."""

            import sys

            python_command = (
                'from keyringrs import Entry;' f'print(Entry("aiida", "{self._computer.uuid}").get_password(), end="")'
            )
            return f"{sys.executable} -c '{python_command}'"

    @property
    def password_manager(self) -> ComputerPasswordManager:
        """Returns the manager of the password associated to this computer stored in system's secure storage."""
        return self.ComputerPasswordManager(self)


class BackendComputerCollection(BackendCollection[BackendComputer]):
    """The collection of Computer entries."""

    ENTITY_CLASS = BackendComputer

    @abc.abstractmethod
    def delete(self, pk: int) -> None:
        """Delete an entry with the given pk

        :param pk: the pk of the entry to delete
        """
