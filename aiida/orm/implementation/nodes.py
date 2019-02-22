# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Abstract BackendNode and BackendNodeCollection implementation."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import abc
import six

from . import backends

__all__ = ('BackendNode', 'BackendNodeCollection')


@six.add_metaclass(abc.ABCMeta)
class BackendNode(backends.BackendEntity):
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
        if self.is_stored:
            self._increment_version_number()

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
        if self.is_stored:
            self._increment_version_number()

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
        if self.is_stored:
            self._increment_version_number()

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

    @property
    def version(self):
        """Return the node version.

        :return: the version
        """
        return self._dbmodel.nodeversion

    @property
    def public(self):
        """Return the node public attribute.

        :return: the public attribute
        """
        return self._dbmodel.public

    @property
    def attributes(self):
        """Return the attributes dictionary.

        .. note:: This will fetch all the attributes from the database which can be a heavy operation. If you only need
            the keys or some values, use the iterators `attributes_keys` and `attributes_items`, or the getters
            `get_attribute` and `get_attributes` instead.

        :return: the attributes as a dictionary
        """
        return dict(self.attributes_items())

    @abc.abstractmethod
    def get_attribute(self, key):
        """Return an attribute.

        :param key: name of the attribute
        :return: the value of the attribute
        :raises AttributeError: if the attribute does not exist
        """

    @abc.abstractmethod
    def get_attributes(self, keys):
        """Return a set of attributes.

        :param keys: names of the attributes
        :return: the values of the attributes
        :raises AttributeError: if at least one attribute does not exist
        """

    @abc.abstractmethod
    def set_attribute(self, key, value):
        """Set an attribute to the given value.

        :param key: name of the attribute
        :param value: value of the attribute
        """

    @abc.abstractmethod
    def set_attributes(self, attributes):
        """Set attributes.

        .. note:: This will override any existing attributes that are present in the new dictionary.

        :param attributes: the new attributes to set
        """

    @abc.abstractmethod
    def reset_attributes(self, attributes):
        """Reset the attributes.

        .. note:: This will completely reset any existing attributes and replace them with the new dictionary.

        :param attributes: the new attributes to set
        """

    @abc.abstractmethod
    def delete_attribute(self, key):
        """Delete an attribute.

        :param key: name of the attribute
        :raises AttributeError: if the attribute does not exist
        """

    @abc.abstractmethod
    def delete_attributes(self, keys):
        """Delete multiple attributes.

        .. note:: The implementation should guarantee that all the keys that are to be deleted actually exist or the
            entire operation should be canceled without any change and an ``AttributeError`` should be raised.

        :param keys: names of the attributes to delete
        :raises AttributeError: if at least on of the attribute does not exist
        """

    @abc.abstractmethod
    def clear_attributes(self):
        """Delete all attributes."""

    @abc.abstractmethod
    def attributes_items(self):
        """Return an iterator over the attribute items.

        :return: an iterator with attribute key value pairs
        """

    @abc.abstractmethod
    def attributes_keys(self):
        """Return an iterator over the attribute keys.

        :return: an iterator with attribute keys
        """

    @property
    def extras(self):
        """Return the extras dictionary.

        .. note:: This will fetch all the extras from the database which can be a heavy operation. If you only need
            the keys or some values, use the iterators `extras_keys` and `extras_items`, or the getters `get_extra`
            and `get_extras` instead.

        :return: the extras as a dictionary
        """
        return dict(self.extras_items())

    @abc.abstractmethod
    def get_extra(self, key):
        """Return an extra.

        :param key: name of the extra
        :return: the value of the extra
        :raises AttributeError: if the extra does not exist
        """

    @abc.abstractmethod
    def get_extras(self, keys):
        """Return a set of extras.

        :param keys: names of the extras
        :return: the values of the extras
        :raises AttributeError: if at least one extra does not exist
        """

    @abc.abstractmethod
    def set_extra(self, key, value, increase_version=True):
        """Set an extra to the given value.

        :param key: name of the extra
        :param value: value of the extra
        :param increase_version: boolean, if True will increase the node version upon successfully setting the extra
        """

    @abc.abstractmethod
    def set_extras(self, extras):
        """Set extras.

        .. note:: This will override any existing extras that are present in the new dictionary.

        :param extras: the new extras to set
        """

    @abc.abstractmethod
    def reset_extras(self, extras):
        """Reset the extras.

        .. note:: This will completely reset any existing extras and replace them with the new dictionary.

        :param extras: the new extras to set
        """

    @abc.abstractmethod
    def delete_extra(self, key):
        """Delete an extra.

        :param key: name of the extra
        :raises AttributeError: if the extra does not exist
        """

    @abc.abstractmethod
    def delete_extras(self, keys):
        """Delete multiple extras.

        .. note:: The implementation should guarantee that all the keys that are to be deleted actually exist or the
            entire operation should be canceled without any change and an ``AttributeError`` should be raised.

        :param keys: names of the extras to delete
        :raises AttributeError: if at least on of the extra does not exist
        """

    @abc.abstractmethod
    def clear_extras(self):
        """Delete all extras."""

    @abc.abstractmethod
    def extras_items(self):
        """Return an iterator over the extra items.

        :return: an iterator with extra key value pairs
        """

    @abc.abstractmethod
    def extras_keys(self):
        """Return an iterator over the attribute keys.

        :return: an iterator with attribute keys
        """

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
    def store(self, attributes=None, links=None, with_transaction=True):
        """Store the node in the database.

        :param attributes: optional attributes to set before storing, will override any existing attributes
        :param links: optional links to add before storing
        :parameter with_transaction: if False, do not use a transaction because the caller will already have opened one.
        """

    @abc.abstractmethod
    def _increment_version_number(self):
        """Increment the node version number of this node by one directly in the database."""


@six.add_metaclass(abc.ABCMeta)
class BackendNodeCollection(backends.BackendCollection[BackendNode]):
    """The collection of `BackendNode` entries."""

    # pylint: disable=too-few-public-methods

    ENTITY_CLASS = BackendNode

    @abc.abstractmethod
    def delete(self, pk):
        """Remove a Node entry from the collection with the given id

        :param pk: id of the node to delete
        """
