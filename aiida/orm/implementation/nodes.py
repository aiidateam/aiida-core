# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend specific computer objects and methods"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import abc
import six

from . import backends

__all__ = 'BackendNode', 'BackendNodeCollection'


@six.add_metaclass(abc.ABCMeta)
class BackendNode(backends.BackendEntity):
    """
    Backend node class
    """

    # pylint: disable=too-many-public-methods

    @abc.abstractproperty
    def nodeversion(self):
        """
        Get the version number for this node

        :return: the version number
        :rtype: int
        """

    @abc.abstractmethod
    def increment_version_number(self):
        """
        Increment the version number of this node by one
        """

    @abc.abstractproperty
    def uuid(self):
        """
        The node UUID

        :return: the uuid
        """

    @abc.abstractmethod
    def get_computer(self):
        """
        Get the computer associated to the node.

        :return: the Computer object or None.
        """

    @abc.abstractmethod
    def set_computer(self, computer):
        """
        Set the backend computer

        :param computer: the computer to set for this node
        :type computer: :class:`aiida.orm.implementation.Computer`
        """

    @abc.abstractmethod
    def get_user(self):
        """
        Get the node user

        :return: the node user
        :rtype: :class:`aiida.orm.implementation.User`
        """

    @abc.abstractmethod
    def set_user(self, user):
        """
        Set the node user

        :param user: the new user
        :type user: :class:`aiida.orm.implementation.User`
        """

    # region Attributes

    @abc.abstractmethod
    def attrs(self):
        """
        The attribute keys

        :return: a generator of the keys
        """

    @abc.abstractmethod
    def iterattrs(self):
        """
        Get an iterator to all the attributes

        :return: the attributes iterator
        """

    @abc.abstractmethod
    def set_attr(self, key, value):
        """
        Set an attribute on this node

        :param key: key name
        :type key: str
        :param value: the value
        """

    @abc.abstractmethod
    def del_attr(self, key):
        """
        Delete an attribute from this node

        :param key: the attribute key
        :type key: str
        """

    @abc.abstractmethod
    def get_attr(self, key):
        """
        Get an attribute from this node

        :param key: the attribute key
        :type key: str
        :return: the attribute value
        """

    # endregion

    # region Extras

    @abc.abstractmethod
    def iterextras(self):
        """
        Get an iterator to the extras

        :return: the extras iterator
        """

    @abc.abstractmethod
    def set_extra(self, key, value, exclusive=False):
        """
        Set an extra on this node

        :param key: the extra key
        :type key: str
        :param value: the extra value
        :param exclusive:
        """

    @abc.abstractmethod
    def get_extra(self, key):
        """
        Get an extra for the node

        :param key: the extra key
        :type key: str
        :return: the extra value
        """

    @abc.abstractmethod
    def del_extra(self, key):
        """
        Delete an extra

        :param key: the extra to delete
        :type key: str
        """

    @abc.abstractmethod
    def reset_extras(self, new_extras):
        """
        Reset all the extras to a new dictionary

        :param new_extras: the dictionary to set the extras to
        :type new_extras: dict
        """

    # endregion

    # region Links

    @abc.abstractmethod
    def get_input_links(self, link_type):
        """
        Get the inputs linked by the given link type

        :param link_type: the input links type
        :return: a list of input backend entities
        """

    @abc.abstractmethod
    def get_output_links(self, link_type):
        """
        Get the outputs linked by the given link type

        :param link_type: the output links type
        :return: a list of output backend entities
        """

    @abc.abstractmethod
    def add_link_from(self, src, link_type, label):
        """
        Add an incoming link from a given source node

        :param src: the source node
        :type src: :class:`aiida.orm.implementation.Node`
        :param link_type: the link type
        :param label: the link label
        """

    @abc.abstractmethod
    def remove_link_from(self, label):
        """
        Remove an incoming link with the given label

        :param label: the label of the link to remove
        """

    @abc.abstractmethod
    def replace_link_from(self, src, link_type, label):
        """
        Replace an existing link

        :param src: the source node
        :type src: :class:`aiida.orm.implementation.Node`
        :param link_type: the link type
        :param label: the link label
        """

    # endregion


@six.add_metaclass(abc.ABCMeta)
class BackendNodeCollection(backends.BackendCollection[BackendNode]):
    """The collection of Computer entries."""

    # pylint: disable=too-few-public-methods

    ENTITY_CLASS = BackendNode
