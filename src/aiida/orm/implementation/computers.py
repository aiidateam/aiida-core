###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend specific computer objects and methods"""

import abc
import logging
from typing import Any, Dict

from .entities import BackendCollection, BackendEntity

__all__ = ('BackendComputer', 'BackendComputerCollection')


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
    def set_label(self, val: str) -> None:
        """Set the (unique) label of the computer."""

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Return the description of the computer."""

    @abc.abstractmethod
    def set_description(self, val: str) -> None:
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


class BackendComputerCollection(BackendCollection[BackendComputer]):
    """The collection of Computer entries."""

    ENTITY_CLASS = BackendComputer

    @abc.abstractmethod
    def delete(self, pk: int) -> None:
        """Delete an entry with the given pk

        :param pk: the pk of the entry to delete
        """

    @abc.abstractmethod
    def list_names(self) -> list[tuple[str]]:
        """Return a list with all the labels of the computers in the DB."""
