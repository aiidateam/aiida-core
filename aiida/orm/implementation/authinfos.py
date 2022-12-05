# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the backend implementation of the `AuthInfo` ORM class."""
import abc
from typing import TYPE_CHECKING, Any, Dict

from .entities import BackendCollection, BackendEntity

if TYPE_CHECKING:
    from .computers import BackendComputer
    from .users import BackendUser

__all__ = ('BackendAuthInfo', 'BackendAuthInfoCollection')


class BackendAuthInfo(BackendEntity):
    """Backend implementation for the `AuthInfo` ORM class.

    An authinfo is a set of credentials that can be used to authenticate to a remote computer.
    """

    METADATA_WORKDIR = 'workdir'

    @property
    @abc.abstractmethod
    def enabled(self) -> bool:
        """Return whether this instance is enabled.

        :return: boolean, True if enabled, False otherwise
        """

    @enabled.setter
    @abc.abstractmethod
    def enabled(self, value: bool) -> None:
        """Set the enabled state

        :param enabled: boolean, True to enable the instance, False to disable it
        """

    @property
    @abc.abstractmethod
    def computer(self) -> 'BackendComputer':
        """Return the computer associated with this instance."""

    @property
    @abc.abstractmethod
    def user(self) -> 'BackendUser':
        """Return the user associated with this instance."""

    @abc.abstractmethod
    def get_auth_params(self) -> Dict[str, Any]:
        """Return the dictionary of authentication parameters

        :return: a dictionary with authentication parameters
        """

    @abc.abstractmethod
    def set_auth_params(self, auth_params: Dict[str, Any]) -> None:
        """Set the dictionary of authentication parameters

        :param auth_params: a dictionary with authentication parameters
        """

    @abc.abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return the dictionary of metadata

        :return: a dictionary with metadata
        """

    @abc.abstractmethod
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set the dictionary of metadata

        :param metadata: a dictionary with metadata
        """


class BackendAuthInfoCollection(BackendCollection[BackendAuthInfo]):
    """The collection of backend `AuthInfo` entries."""

    ENTITY_CLASS = BackendAuthInfo

    @abc.abstractmethod
    def delete(self, pk: int) -> None:
        """Delete an entry from the collection.

        :param pk: the pk of the entry to delete
        """
