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

from . import backends

__all__ = ('BackendNode', 'BackendNodeCollection')


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

    @abc.abstractproperty
    def attributes(self):
        """Return the complete attributes dictionary.

        .. warning:: While the node is unstored, this will return references of the attributes on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned
            attributes will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you
            only need the keys or some values, use the iterators `attributes_keys` and `attributes_items`, or the
            getters `get_attribute` and `get_attribute_many` instead.

        :return: the attributes as a dictionary
        """

    @abc.abstractmethod
    def get_attribute(self, key):
        """Return the value of an attribute.

        .. warning:: While the node is unstored, this will return a reference of the attribute on the database model,
            meaning that changes on the returned value (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned
            attribute will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods.

        :param key: name of the attribute
        :return: the value of the attribute
        :raises AttributeError: if the attribute does not exist
        """

    @abc.abstractmethod
    def get_attribute_many(self, keys):
        """Return the values of multiple attributes.

        .. warning:: While the node is unstored, this will return references of the attributes on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned
            attributes will be a deep copy and mutations of the database attributes will have to go through the
            appropriate set methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you
            only need the keys or some values, use the iterators `attributes_keys` and `attributes_items`, or the
            getters `get_attribute` and `get_attribute_many` instead.

        :param keys: a list of attribute names
        :return: a list of attribute values
        :raises AttributeError: if at least one attribute does not exist
        """

    @abc.abstractmethod
    def set_attribute(self, key, value):
        """Set an attribute to the given value.

        :param key: name of the attribute
        :param value: value of the attribute
        """

    @abc.abstractmethod
    def set_attribute_many(self, attributes):
        """Set multiple attributes.

        .. note:: This will override any existing attributes that are present in the new dictionary.

        :param attributes: a dictionary with the attributes to set
        """

    @abc.abstractmethod
    def reset_attributes(self, attributes):
        """Reset the attributes.

        .. note:: This will completely clear any existing attributes and replace them with the new dictionary.

        :param attributes: a dictionary with the attributes to set
        """

    @abc.abstractmethod
    def delete_attribute(self, key):
        """Delete an attribute.

        :param key: name of the attribute
        :raises AttributeError: if the attribute does not exist
        """

    @abc.abstractmethod
    def delete_attribute_many(self, keys):
        """Delete multiple attributes.

        :param keys: names of the attributes to delete
        :raises AttributeError: if at least one of the attribute does not exist
        """

    @abc.abstractmethod
    def clear_attributes(self):
        """Delete all attributes."""

    @abc.abstractmethod
    def attributes_items(self):
        """Return an iterator over the attributes.

        :return: an iterator with attribute key value pairs
        """

    @abc.abstractmethod
    def attributes_keys(self):
        """Return an iterator over the attribute keys.

        :return: an iterator with attribute keys
        """

    @abc.abstractproperty
    def extras(self):
        """Return the complete extras dictionary.

        .. warning:: While the node is unstored, this will return references of the extras on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned extras
            will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you only need the keys
            or some values, use the iterators `extras_keys` and `extras_items`, or the getters `get_extra` and
            `get_extra_many` instead.

        :return: the extras as a dictionary
        """

    @abc.abstractmethod
    def get_extra(self, key):
        """Return the value of an extra.

        .. warning:: While the node is unstored, this will return a reference of the extra on the database model,
            meaning that changes on the returned value (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned extra
            will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods.

        :param key: name of the extra
        :return: the value of the extra
        :raises AttributeError: if the extra does not exist
        """

    @abc.abstractmethod
    def get_extra_many(self, keys):
        """Return the values of multiple extras.

        .. warning:: While the node is unstored, this will return references of the extras on the database model,
            meaning that changes on the returned values (if they are mutable themselves, e.g. a list or dictionary) will
            automatically be reflected on the database model as well. As soon as the node is stored, the returned extras
            will be a deep copy and mutations of the database extras will have to go through the appropriate set
            methods. Therefore, once stored, retrieving a deep copy can be a heavy operation. If you only need the keys
            or some values, use the iterators `extras_keys` and `extras_items`, or the getters `get_extra` and
            `get_extra_many` instead.

        :param keys: a list of extra names
        :return: a list of extra values
        :raises AttributeError: if at least one extra does not exist
        """

    @abc.abstractmethod
    def set_extra(self, key, value):
        """Set an extra to the given value.

        :param key: name of the extra
        :param value: value of the extra
        """

    @abc.abstractmethod
    def set_extra_many(self, extras):
        """Set multiple extras.

        .. note:: This will override any existing extras that are present in the new dictionary.

        :param extras: a dictionary with the extras to set
        """

    @abc.abstractmethod
    def reset_extras(self, extras):
        """Reset the extras.

        .. note:: This will completely clear any existing extras and replace them with the new dictionary.

        :param extras: a dictionary with the extras to set
        """

    @abc.abstractmethod
    def delete_extra(self, key):
        """Delete an extra.

        :param key: name of the extra
        :raises AttributeError: if the extra does not exist
        """

    @abc.abstractmethod
    def delete_extra_many(self, keys):
        """Delete multiple extras.

        :param keys: names of the extras to delete
        :raises AttributeError: if at least one of the extra does not exist
        """

    @abc.abstractmethod
    def clear_extras(self):
        """Delete all extras."""

    @abc.abstractmethod
    def extras_items(self):
        """Return an iterator over the extras.

        :return: an iterator with extra key value pairs
        """

    @abc.abstractmethod
    def extras_keys(self):
        """Return an iterator over the extra keys.

        :return: an iterator with extra keys
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
    def store(self, links=None, with_transaction=True, clean=True):
        """Store the node in the database.

        :param links: optional links to add before storing
        :param with_transaction: if False, do not use a transaction because the caller will already have opened one.
        :param clean: boolean, if True, will clean the attributes and extras before attempting to store
        """


class BackendNodeCollection(backends.BackendCollection[BackendNode]):
    """The collection of `BackendNode` entries."""

    # pylint: disable=too-few-public-methods

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
