# -*- coding: utf-8 -*-
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

from .entities import BackendEntity, BackendCollection

__all__ = ('BackendComputer', 'BackendComputerCollection')


class BackendComputer(BackendEntity):
    """
    Base class to map a node in the DB + its permanent repository counterpart.

    Stores attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything only on store().
    After the call to store(), attributes cannot be changed.

    Only after storing (or upon loading from uuid) metadata can be modified
    and in this case they are directly set on the db.

    In the plugin, also set the _plugin_type_string, to be set in the DB in the 'type' field.
    """
    # pylint: disable=too-many-public-methods

    _logger = logging.getLogger(__name__)

    @abc.abstractproperty
    def is_stored(self):
        """
        Is the computer stored?

        :return: True if stored, False otherwise
        :rtype: bool
        """

    @abc.abstractproperty
    def name(self):
        pass

    @abc.abstractproperty
    def description(self):
        pass

    @abc.abstractproperty
    def hostname(self):
        pass

    @abc.abstractmethod
    def get_metadata(self):
        pass

    @abc.abstractmethod
    def set_metadata(self, metadata):
        """
        Set the metadata.

        .. note: You still need to call the .store() method to actually save
           data to the database! (The store method can be called multiple
           times, differently from AiiDA Node objects).
        """

    @abc.abstractmethod
    def get_name(self):
        pass

    @abc.abstractmethod
    def set_name(self, val):
        pass

    def get_hostname(self):
        """
        Get this computer hostname
        :rtype: str
        """

    @abc.abstractmethod
    def set_hostname(self, val):
        """
        Set the hostname of this computer
        :param val: The new hostname
        :type val: str
        """

    @abc.abstractmethod
    def get_description(self):
        pass

    @abc.abstractmethod
    def set_description(self, val):
        pass

    @abc.abstractmethod
    def get_scheduler_type(self):
        pass

    @abc.abstractmethod
    def set_scheduler_type(self, scheduler_type):
        pass

    @abc.abstractmethod
    def get_transport_type(self):
        pass

    @abc.abstractmethod
    def set_transport_type(self, transport_type):
        pass


class BackendComputerCollection(BackendCollection[BackendComputer]):
    """The collection of Computer entries."""

    ENTITY_CLASS = BackendComputer

    @abc.abstractmethod
    def delete(self, pk):
        """
        Delete an entry with the given pk

        :param pk: the pk of the entry to delete
        """
