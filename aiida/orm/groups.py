# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA Group entites"""
from abc import ABCMeta
import warnings

from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.manage.manager import get_manager

from . import convert
from . import entities
from . import users

__all__ = ('Group', 'AutoGroup', 'ImportGroup', 'UpfFamily')


def load_group_class(type_string):
    """Load the sub class of `Group` that corresponds to the given `type_string`.

    .. note:: will fall back on `aiida.orm.groups.Group` if `type_string` cannot be resolved to loadable entry point.

    :param type_string: the entry point name of the `Group` sub class
    :return: sub class of `Group` registered through an entry point
    """
    from aiida.common.exceptions import EntryPointError
    from aiida.plugins.entry_point import load_entry_point

    try:
        group_class = load_entry_point('aiida.groups', type_string)
    except EntryPointError:
        message = f'could not load entry point `{type_string}`, falling back onto `Group` base class.'
        warnings.warn(message)  # pylint: disable=no-member
        group_class = Group

    return group_class


class GroupMeta(ABCMeta):
    """Meta class for `aiida.orm.groups.Group` to automatically set the `type_string` attribute."""

    def __new__(cls, name, bases, namespace, **kwargs):
        from aiida.plugins.entry_point import get_entry_point_from_class

        newcls = ABCMeta.__new__(cls, name, bases, namespace, **kwargs)  # pylint: disable=too-many-function-args

        entry_point_group, entry_point = get_entry_point_from_class(namespace['__module__'], name)

        if entry_point_group is None or entry_point_group != 'aiida.groups':
            newcls._type_string = None
            message = f'no registered entry point for `{name}` so its instances will not be storable.'
            warnings.warn(message)  # pylint: disable=no-member
        else:
            newcls._type_string = entry_point.name  # pylint: disable=protected-access

        return newcls


class Group(entities.Entity, entities.EntityExtrasMixin, metaclass=GroupMeta):
    """An AiiDA ORM implementation of group of nodes."""

    class Collection(entities.Collection):
        """Collection of Groups"""

        def get_or_create(self, label=None, **kwargs):
            """
            Try to retrieve a group from the DB with the given arguments;
            create (and store) a new group if such a group was not present yet.

            :param label: group label
            :type label: str

            :return: (group, created) where group is the group (new or existing,
              in any case already stored) and created is a boolean saying
            :rtype: (:class:`aiida.orm.Group`, bool)
            """
            if not label:
                raise ValueError('Group label must be provided')

            res = self.find(filters={'label': label})

            if not res:
                return self.entity_type(label, backend=self.backend, **kwargs).store(), True

            if len(res) > 1:
                raise exceptions.MultipleObjectsError('More than one groups found in the database')

            return res[0], False

        def delete(self, id):  # pylint: disable=invalid-name, redefined-builtin
            """
            Delete a group

            :param id: the id of the group to delete
            """
            self._backend.groups.delete(id)

    def __init__(self, label=None, user=None, description='', type_string=None, backend=None):
        """
        Create a new group. Either pass a dbgroup parameter, to reload
        a group from the DB (and then, no further parameters are allowed),
        or pass the parameters for the Group creation.

        :param label: The group label, required on creation
        :type label: str

        :param description: The group description (by default, an empty string)
        :type description: str

        :param user: The owner of the group (by default, the automatic user)
        :type user: :class:`aiida.orm.User`

        :param type_string: a string identifying the type of group (by default,
            an empty string, indicating an user-defined group.
        :type type_string: str
        """
        if not label:
            raise ValueError('Group label must be provided')

        backend = backend or get_manager().get_backend()
        user = user or users.User.objects(backend).get_default()
        type_check(user, users.User)
        type_string = self._type_string

        model = backend.groups.create(
            label=label, user=user.backend_entity, description=description, type_string=type_string
        )
        super().__init__(model)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self)}>'

    def __str__(self):
        if self.type_string:
            return f'"{self.label}" [type {self.type_string}], of user {self.user.email}'

        return f'"{self.label}" [user-defined], of user {self.user.email}'

    def store(self):
        """Verify that the group is allowed to be stored, which is the case along as `type_string` is set."""
        if self._type_string is None:
            raise exceptions.StoringNotAllowed('`type_string` is `None` so the group cannot be stored.')

        return super().store()

    @property
    def label(self):
        """
        :return: the label of the group as a string
        """
        return self._backend_entity.label

    @label.setter
    def label(self, label):
        """
        Attempt to change the label of the group instance. If the group is already stored
        and the another group of the same type already exists with the desired label, a
        UniquenessError will be raised

        :param label: the new group label
        :type label: str

        :raises aiida.common.UniquenessError: if another group of same type and label already exists
        """
        self._backend_entity.label = label

    @property
    def description(self):
        """
        :return: the description of the group as a string
        :rtype: str
        """
        return self._backend_entity.description

    @description.setter
    def description(self, description):
        """
        :param description: the description of the group as a string
        :type description: str

        """
        self._backend_entity.description = description

    @property
    def type_string(self):
        """
        :return: the string defining the type of the group
        """
        return self._backend_entity.type_string

    @property
    def user(self):
        """
        :return: the user associated with this group
        """
        return users.User.from_backend_entity(self._backend_entity.user)

    @user.setter
    def user(self, user):
        """Set the user.

        :param user: the user
        :type user: :class:`aiida.orm.User`
        """
        type_check(user, users.User)
        self._backend_entity.user = user.backend_entity

    @property
    def uuid(self):
        """
        :return: a string with the uuid
        :rtype: str
        """
        return self._backend_entity.uuid

    def count(self):
        """Return the number of entities in this group.

        :return: integer number of entities contained within the group
        :rtype: int
        """
        return self._backend_entity.count()

    @property
    def nodes(self):
        """
        Return a generator/iterator that iterates over all nodes and returns
        the respective AiiDA subclasses of Node, and also allows to ask for
        the number of nodes in the group using len().

        :rtype: :class:`aiida.orm.convert.ConvertIterator`
        """
        return convert.ConvertIterator(self._backend_entity.nodes)

    @property
    def is_empty(self):
        """Return whether the group is empty, i.e. it does not contain any nodes.

        :return: True if it contains no nodes, False otherwise
        :rtype: bool
        """
        try:
            self.nodes[0]
        except IndexError:
            return True
        else:
            return False

    def clear(self):
        """Remove all the nodes from this group."""
        return self._backend_entity.clear()

    def add_nodes(self, nodes):
        """Add a node or a set of nodes to the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a single `Node` or a list of `Nodes`
        :type nodes: :class:`aiida.orm.Node` or list
        """
        from .nodes import Node

        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot add nodes to an unstored group')

        # Cannot use `collections.Iterable` here, because that would also match iterable `Node` sub classes like `List`
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]

        for node in nodes:
            type_check(node, Node)

        self._backend_entity.add_nodes([node.backend_entity for node in nodes])

    def remove_nodes(self, nodes):
        """Remove a node or a set of nodes to the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a single `Node` or a list of `Nodes`
        :type nodes: :class:`aiida.orm.Node` or list
        """
        from .nodes import Node

        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot add nodes to an unstored group')

        # Cannot use `collections.Iterable` here, because that would also match iterable `Node` sub classes like `List`
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]

        for node in nodes:
            type_check(node, Node)

        self._backend_entity.remove_nodes([node.backend_entity for node in nodes])

    def is_user_defined(self):
        """
        :return: True if the group is user defined, False otherwise
        :rtype: bool
        """
        return not self.type_string


class AutoGroup(Group):
    """Group to be used to contain selected nodes generated while `aiida.orm.autogroup.CURRENT_AUTOGROUP` is set."""


class ImportGroup(Group):
    """Group to be used to contain all nodes from an export archive that has been imported."""


class UpfFamily(Group):
    """Group that represents a pseudo potential family containing `UpfData` nodes."""
