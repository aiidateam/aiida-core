# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" AiiDA Group entites"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from enum import Enum
import warnings
import six

from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.manage.manager import get_manager

from . import convert
from . import entities
from . import users

__all__ = ('Group', 'GroupTypeString')


class GroupTypeString(Enum):
    """A simple enum of allowed group type strings."""

    UPFGROUP_TYPE = 'data.upf'
    IMPORTGROUP_TYPE = 'auto.import'
    VERDIAUTOGROUP_TYPE = 'auto.run'
    USER = 'user'


class Group(entities.Entity):
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

            filters = {'label': label}

            if 'type_string' in kwargs:
                if not isinstance(kwargs['type_string'], six.string_types):
                    raise exceptions.ValidationError(
                        'type_string must be {}, you provided an object of type '
                        '{}'.format(str, type(kwargs['type_string']))
                    )

                filters['type_string'] = kwargs['type_string']

            res = self.find(filters=filters)

            if not res:
                return Group(label, backend=self.backend, **kwargs).store(), True

            if len(res) > 1:
                raise exceptions.MultipleObjectsError('More than one groups found in the database')

            return res[0], False

        def delete(self, id):  # pylint: disable=invalid-name, redefined-builtin
            """
            Delete a group

            :param id: the id of the group to delete
            """
            self._backend.groups.delete(id)

    def __init__(self, label=None, user=None, description='', type_string=GroupTypeString.USER.value, backend=None):
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

        # Check that chosen type_string is allowed
        if not isinstance(type_string, six.string_types):
            raise exceptions.ValidationError(
                'type_string must be {}, you provided an object of type '
                '{}'.format(str, type(type_string))
            )

        backend = backend or get_manager().get_backend()
        user = user or users.User.objects(backend).get_default()
        type_check(user, users.User)

        model = backend.groups.create(
            label=label, user=user.backend_entity, description=description, type_string=type_string
        )
        super(Group, self).__init__(model)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if self.type_string:
            return '"{}" [type {}], of user {}'.format(self.label, self.type_string, self.user.email)

        return '"{}" [user-defined], of user {}'.format(self.label, self.user.email)

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

    @classmethod
    def get(cls, **kwargs):
        """
        Custom get for group which can be used to get a group with the given attributes

        :param kwargs: the attributes to match the group to

        :return: the group
        :type nodes: :class:`aiida.orm.Node` or list
        """
        from aiida.orm import QueryBuilder

        filters = {}
        if 'type_string' in kwargs:
            if not isinstance(kwargs['type_string'], six.string_types):
                raise exceptions.ValidationError(
                    'type_string must be {}, you provided an object of type '
                    '{}'.format(str, type(kwargs['type_string']))
                )

        query = QueryBuilder()
        for key, val in kwargs.items():
            filters[key] = val

        query.append(cls, filters=filters)
        results = query.all()
        if len(results) > 1:
            raise exceptions.MultipleObjectsError("Found {} groups matching criteria '{}'".format(len(results), kwargs))
        if not results:
            raise exceptions.NotExistent("No group found matching criteria '{}'".format(kwargs))
        return results[0][0]

    def is_user_defined(self):
        """
        :return: True if the group is user defined, False otherwise
        :rtype: bool
        """
        return not self.type_string

    @staticmethod
    def get_schema():
        """
        Every node property contains:
            - display_name: display name of the property
            - help text: short help text of the property
            - is_foreign_key: is the property foreign key to other type of the node
            - type: type of the property. e.g. str, dict, int

        :return: schema of the group
        :rtype: dict

        .. deprecated:: 1.0.0

            Will be removed in `v2.0.0`.
            Use :meth:`~aiida.restapi.translator.base.BaseTranslator.get_projectable_properties` instead.

        """
        message = 'method is deprecated, use' \
            '`aiida.restapi.translator.base.BaseTranslator.get_projectable_properties` instead'
        warnings.warn(message, AiidaDeprecationWarning)  # pylint: disable=no-member

        return {
            'description': {
                'display_name': 'Description',
                'help_text': 'Short description of the group',
                'is_foreign_key': False,
                'type': 'str'
            },
            'id': {
                'display_name': 'Id',
                'help_text': 'Id of the object',
                'is_foreign_key': False,
                'type': 'int'
            },
            'label': {
                'display_name': 'Label',
                'help_text': 'Name of the object',
                'is_foreign_key': False,
                'type': 'str'
            },
            'type_string': {
                'display_name': 'Type_string',
                'help_text': 'Type of the group',
                'is_foreign_key': False,
                'type': 'str'
            },
            'user_id': {
                'display_name': 'Id of creator',
                'help_text': 'Id of the user that created the node',
                'is_foreign_key': True,
                'related_column': 'id',
                'related_resource': '_dbusers',
                'type': 'int'
            },
            'uuid': {
                'display_name': 'Unique ID',
                'help_text': 'Universally Unique Identifier',
                'is_foreign_key': False,
                'type': 'unicode'
            }
        }
