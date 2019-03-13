# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend group module"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import abc
import six

from aiida.common import exceptions

from . import backends
from .nodes import BackendNode

__all__ = ('BackendGroup', 'BackendGroupCollection')


@six.add_metaclass(abc.ABCMeta)
class BackendGroup(backends.BackendEntity):
    """
    An AiiDA ORM implementation of group of nodes.
    """

    @abc.abstractproperty
    def label(self):
        """
        :return: the name of the group as a string
        """

    @abc.abstractproperty
    @label.setter
    def label(self, name):
        """
        Attempt to change the name of the group instance. If the group is already stored
        and the another group of the same type already exists with the desired name, a
        UniquenessError will be raised

        :param name: the new group name
        :raises aiida.common.UniquenessError: if another group of same type and name already exists
        """

    @abc.abstractproperty
    def description(self):
        """
        :return: the description of the group as a string
        """

    @description.setter
    @abc.abstractmethod
    def description(self, value):
        """
        :return: the description of the group as a string
        """

    @abc.abstractproperty
    def type_string(self):
        """
        :return: the string defining the type of the group
        """

    @abc.abstractproperty
    def user(self):
        """
        :return: a backend user object, representing the user associated to this group.
        :rtype: :class:`aiida.orm.implementation.BackendUser`
        """

    @abc.abstractproperty
    def id(self):  # pylint: disable=invalid-name
        """
        :return: the principal key (the ID) as an integer, or None if the node was not stored yet
        """

    @abc.abstractproperty
    def uuid(self):
        """
        :return: a string with the uuid
        """

    @classmethod
    def create(cls, *args, **kwargs):
        """
        Create and store a new group.

        Note: This method does not check for presence of the group.
        You may want to use get_or_create().

        :return: group
        """
        return cls(*args, **kwargs).store()

    @classmethod
    def get_or_create(cls, *args, **kwargs):
        """
        Try to retrieve a group from the DB with the given arguments;
        create (and store) a new group if such a group was not present yet.

        :return: (group, created) where group is the group (new or existing,
          in any case already stored) and created is a boolean saying
        """
        res = cls.query(name=kwargs.get("name"), type_string=kwargs.get("type_string"))

        if not res:
            return cls.create(*args, **kwargs), True

        if len(res) > 1:
            raise exceptions.MultipleObjectsError("More than one groups found in the database")

        return res[0], False

    @abc.abstractmethod
    def __int__(self):
        """
        Convert the class to an integer. This is needed to allow querying
        with Django. Be careful, though, not to pass it to a wrong field!
        This only returns the local DB principal key (pk) value.

        :return: the integer pk of the node or None if not stored.
        """

    @abc.abstractproperty
    def is_stored(self):
        """
        :return: True if the respective DbNode has been already saved in the DB, False otherwise
        """

    @abc.abstractmethod
    def store(self):
        pass

    @abc.abstractproperty
    def nodes(self):
        """
        Return a generator/iterator that iterates over all nodes and returns
        the respective AiiDA subclasses of Node, and also allows to ask for
        the number of nodes in the group using len().
        """

    @abc.abstractproperty
    def count(self):
        """Return the number of entities in this group.

        :return: integer number of entities contained within the group
        """

    def add_nodes(self, nodes, **kwargs):  # pylint: disable=unused-argument
        """Add a set of nodes to the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a list of `BackendNode` instances to be added to this group
        """
        if not self.is_stored:
            raise ValueError('group has to be stored before nodes can be added')

        if not isinstance(nodes, (list, tuple)):
            raise TypeError('nodes has to be a list or tuple')

        if any([not isinstance(node, BackendNode) for node in nodes]):
            raise TypeError('nodes have to be of type {}'.format(BackendNode))

    def remove_nodes(self, nodes):
        """Remove a set of nodes from the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a list of `BackendNode` instances to be removed from this group
        """
        if not self.is_stored:
            raise ValueError('group has to be stored before nodes can be removed')

        if not isinstance(nodes, (list, tuple)):
            raise TypeError('nodes has to be a list or tuple')

        if any([not isinstance(node, BackendNode) for node in nodes]):
            raise TypeError('nodes have to be of type {}'.format(BackendNode))

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if self.type_string:
            return '"{}" [type {}], of user {}'.format(self.label, self.type_string, self.user.email)

        return '"{}" [user-defined], of user {}'.format(self.label, self.user.email)


@six.add_metaclass(abc.ABCMeta)
class BackendGroupCollection(backends.BackendCollection[BackendGroup]):
    """The collection of Group entries."""

    ENTITY_CLASS = BackendGroup

    @abc.abstractmethod
    # pylint: disable=too-many-arguments
    def query(self,
              label=None,
              type_string=None,
              pk=None,
              uuid=None,
              nodes=None,
              user=None,
              node_attributes=None,
              past_days=None,
              label_filters=None,
              **kwargs):
        """
        Query for groups.

        :note: By default, query for user-defined groups only (type_string=="").
            If you want to query for all type of groups, pass type_string=None.
            If you want to query for a specific type of groups, pass a specific
            string as the type_string argument.

        :param name: the name of the group
        :param nodes: a node or list of nodes that belongs to the group (alternatively,
            you can also pass a DbNode or list of DbNodes)
        :param pk: the pk of the group
        :param uuid: the uuid of the group
        :param type_string: the string for the type of node; by default, look
            only for user-defined groups (see note above).
        :param user: by default, query for groups of all users; if specified,
            must be a DbUser object, or a string for the user email.
        :param past_days: by default, query for all groups; if specified, query
            the groups created in the last past_days. Must be a datetime object.
        :param name_filters: dictionary that can contain 'startswith', 'endswith' or 'contains' as keys
        :param node_attributes: if not None, must be a dictionary with
            format {k: v}. It will filter and return only groups where there
            is at least a node with an attribute with key=k and value=v.
            Different keys of the dictionary are joined with AND (that is, the
            group should satisfy all requirements.
            v can be a base data type (str, bool, int, float, ...)
            If it is a list or iterable, that the condition is checked so that
            there should be at least a node in the group with key=k and
            value=each of the values of the iterable.
        :param kwargs: any other filter to be passed to DbGroup.objects.filter

            Example: if ``node_attributes = {'elements': ['Ba', 'Ti'], 'md5sum': 'xxx'}``,
                it will find groups that contain the node with md5sum = 'xxx', and moreover
                contain at least one node for element 'Ba' and one node for element 'Ti'.

        """

    def get(self, **filters):
        """
        Get the group matching the given filters

        :param filters: the attributes of the group to get
        :return: the group
        :rtype: :class:`aiida.orm.implementation.BackendGroup`
        """
        results = self.query(**filters)
        if len(results) > 1:
            raise exceptions.MultipleObjectsError("Found multiple groups matching criteria '{}'".format(filters))
        if not results:
            raise exceptions.NotExistent("No group bound matching criteria '{}'".format(filters))
        return results[0]

    @abc.abstractmethod
    def delete(self, id):  # pylint: disable=redefined-builtin, invalid-name
        """
        Delete a group with the given id

        :param id: the id of the group to delete
        """
