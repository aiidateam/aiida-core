# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Abstract BackendNode and BackendNodeCollection implementation."""

import abc

from .entities import BackendEntity, BackendCollection, BackendEntityAttributesMixin, BackendEntityExtrasMixin

__all__ = ('BackendNode', 'BackendNodeCollection')


class BackendNode(BackendEntity, BackendEntityExtrasMixin, BackendEntityAttributesMixin, metaclass=abc.ABCMeta):
    """Wrapper around a `DbNode` instance to set and retrieve data independent of the database implementation."""

    # pylint: disable=too-many-public-methods

    @abc.abstractmethod
    def clone(self):
        """Return an unstored clone of ourselves.

        :return: an unstored `BackendNode` with the exact same attributes and extras as self
        """

    @property
    def uuid(self):
        """Return the node UUID.

        :return: the string representation of the UUID
        :rtype: str or None
        """
        if self._dbmodel.uuid:
            return str(self._dbmodel.uuid)

        return None

    @property
    def node_type(self):
        """Return the node type.

        :return: the node type
        """
        return self._dbmodel.node_type

    @property
    def process_type(self):
        """Return the node process type.

        :return: the process type
        """
        return self._dbmodel.process_type

    @process_type.setter
    def process_type(self, value):
        """Set the process type.

        :param value: the new value to set
        """
        self._dbmodel.process_type = value

    @property
    def label(self):
        """Return the node label.

        :return: the label
        """
        return self._dbmodel.label

    @label.setter
    def label(self, value):
        """Set the label.

        :param value: the new value to set
        """
        self._dbmodel.label = value

    @property
    def description(self):
        """Return the node description.

        :return: the description
        """
        return self._dbmodel.description

    @description.setter
    def description(self, value):
        """Set the description.

        :param value: the new value to set
        """
        self._dbmodel.description = value

    @abc.abstractproperty
    def computer(self):
        """Return the computer of this node.

        :return: the computer or None
        :rtype: `BackendComputer` or None
        """

    @computer.setter
    @abc.abstractmethod
    def computer(self, computer):
        """Set the computer of this node.

        :param computer: a `BackendComputer`
        """

    @abc.abstractproperty
    def user(self):
        """Return the user of this node.

        :return: the user
        :rtype: `BackendUser`
        """

    @user.setter
    @abc.abstractmethod
    def user(self, user):
        """Set the user of this node.

        :param user: a `BackendUser`
        """

    @property
    def ctime(self):
        """Return the node ctime.

        :return: the ctime
        """
        return self._dbmodel.ctime

    @property
    def mtime(self):
        """Return the node mtime.

        :return: the mtime
        """
        return self._dbmodel.mtime

    @abc.abstractmethod
    def add_incoming(self, source, link_type, link_label):
        """Add a link of the given type from a given node to ourself.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :return: True if the proposed link is allowed, False otherwise
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """

    @abc.abstractmethod
    def store(self, links=None, with_transaction=True, clean=True):  # pylint: disable=arguments-differ
        """Store the node in the database.

        :param links: optional links to add before storing
        :param with_transaction: if False, do not use a transaction because the caller will already have opened one.
        :param clean: boolean, if True, will clean the attributes and extras before attempting to store
        """


class BackendNodeCollection(BackendCollection[BackendNode]):
    """The collection of `BackendNode` entries."""

    ENTITY_CLASS = BackendNode

    @abc.abstractmethod
    def get(self, pk):
        """Return a Node entry from the collection with the given id

        :param pk: id of the node
        """

    @abc.abstractmethod
    def delete(self, pk):
        """Remove a Node entry from the collection with the given id

        :param pk: id of the node to delete
        """
