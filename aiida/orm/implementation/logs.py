# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend group module"""
import abc
from datetime import datetime
from typing import Any, Dict, List

from .entities import BackendCollection, BackendEntity

__all__ = ('BackendLog', 'BackendLogCollection')


class BackendLog(BackendEntity):
    """Backend implementation for the `Log` ORM class.

    A log is a record of logging call for a particular node.
    """

    @property
    @abc.abstractmethod
    def uuid(self) -> str:
        """Return the UUID of the log entry."""

    @property
    @abc.abstractmethod
    def time(self) -> datetime:
        """Return the time corresponding to the log entry."""

    @property
    @abc.abstractmethod
    def loggername(self) -> str:
        """Return the name of the logger that created this entry."""

    @property
    @abc.abstractmethod
    def levelname(self) -> str:
        """Return the name of the log level."""

    @property
    @abc.abstractmethod
    def dbnode_id(self) -> int:
        """Return the id of the object that created the log entry."""

    @property
    @abc.abstractmethod
    def message(self) -> str:
        """Return the message corresponding to the log entry."""

    @property
    @abc.abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return the metadata corresponding to the log entry."""


class BackendLogCollection(BackendCollection[BackendLog]):
    """The collection of Log entries."""

    ENTITY_CLASS = BackendLog

    @abc.abstractmethod
    def delete(self, log_id: int) -> None:
        """
        Remove a Log entry from the collection with the given id

        :param log_id: id of the Log to delete

        :raises TypeError: if ``log_id`` is not an `int`
        :raises `~aiida.common.exceptions.NotExistent`: if Log with ID ``log_id`` is not found
        """

    @abc.abstractmethod
    def delete_all(self) -> None:
        """
        Delete all Log entries.

        :raises `~aiida.common.exceptions.IntegrityError`: if all Logs could not be deleted
        """

    @abc.abstractmethod
    def delete_many(self, filters: dict) -> List[int]:
        """
        Delete Logs based on ``filters``

        :param filters: similar to QueryBuilder filter

        :return: (former) ``PK`` s of deleted Logs

        :raises TypeError: if ``filters`` is not a `dict`
        :raises `~aiida.common.exceptions.ValidationError`: if ``filters`` is empty
        """
