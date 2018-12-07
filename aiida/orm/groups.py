# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" AiiDA Group entites"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from enum import Enum
from aiida.common import exceptions
from aiida.common.utils import type_check
from aiida.cmdline.utils import echo
from aiida.manage import get_manager

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
    """
    An AiiDA ORM implementation of group of nodes.
    """

    class Collection(entities.Collection):
        """Collection of Groups"""

        def get_or_create(self, label, **kwargs):
            """
            Try to retrieve a group from the DB with the given arguments;
            create (and store) a new group if such a group was not present yet.

            :return: (group, created) where group is the group (new or existing,
              in any case already stored) and created is a boolean saying
            """
            filters = {'label': label}
            if 'type_string' in kwargs:
                filters['type_string'] = kwargs['type_string']
                try:
                    GroupTypeString(kwargs['type_string'])
                except ValueError:
                    echo.echo_critical("Group type_string <{}> is not allowed. Allowed type_strings are: "
                                       "{}".format(kwargs['type_string'],
                                                   ', '.join([i.value for i in GroupTypeString])))

            res = self.find(filters=filters)

            if not res:
                return Group(label, backend=self.backend, **kwargs).store(), True
            elif len(res) > 1:
                raise exceptions.MultipleObjectsError("More than one groups found in the database")
            else:
                return res[0], False

        def find(self, filters=None, order_by=None, limit=None):
            """Custom find method for Group to correctly map to backend type_string"""
            # We need to map type_string to type for now because the underlying ORM model
            # for the current backends uses 'type' as the column label instead of type_string
            # A better way to deal with this would be to implement a general way for the query builder
            # to ask the backend class what the mapping between the attribute label and the column label
            # should be.  Probably in the get_column() method...but this requires a bit more thought
            if filters and 'type_string' in filters:
                filters['type_string'] = filters.pop('type_string')

            return super(Group.Collection, self).find(filters=filters, order_by=order_by, limit=limit)

        def delete(self, id):  # pylint: disable=invalid-name, redefined-builtin
            """
            Delete a group

            :param id: the id of the group to delete
            """
            self._backend.groups.delete(id)

    def __init__(self, label, user=None, description='', type_string=GroupTypeString.USER.value, backend=None):
        """
        Create a new group. Either pass a dbgroup parameter, to reload
        ad group from the DB (and then, no further parameters are allowed),
        or pass the parameters for the Group creation.

        :param dbgroup: the dbgroup object, if you want to reload the group
            from the DB rather than creating a new one.
        :param label: The group label, required on creation
        :param description: The group description (by default, an empty string)
        :param user: The owner of the group (by default, the automatic user)
        :param type_string: a string identifying the type of group (by default,
            an empty string, indicating an user-defined group.
        """
        backend = backend or get_manager().get_backend()
        user = user or users.User.objects(backend).get_default()
        type_check(user, users.User)

        # Check that chosen type is allowed
        try:
            GroupTypeString(type_string)
        except ValueError:
            echo.echo_critical("Group type_string <{}> is not allowed. Allowed type_strings are: "
                               "{}".format(type_string, ', '.join([i.value for i in GroupTypeString])))

        model = backend.groups.create(
            label=label, user=user.backend_entity, description=description, type_string=type_string)
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
        :raises UniquenessError: if another group of same type and label already exists
        """
        self._backend_entity.label = label

    @property
    def description(self):
        """
        :return: the description of the group as a string
        """
        return self._backend_entity.description

    @description.setter
    def description(self, description):
        """
        :return: the description of the group as a string
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
        type_check(user, users.User)
        self._backend_entity.user = user.backend_entity

    @property
    def uuid(self):
        """
        :return: a string with the uuid
        """
        return self._backend_entity.uuid

    def add_nodes(self, nodes):
        """
        Add a node or a set of nodes to the group.

        :note: The group must be already stored.

        :note: each of the nodes passed to add_nodes must be already stored.

        :param nodes: a Node or DbNode object to add to the group, or
          a list of Nodes or DbNodes to add.
        """
        self._backend_entity.add_nodes(nodes)

    @property
    def nodes(self):
        """
        Return a generator/iterator that iterates over all nodes and returns
        the respective AiiDA subclasses of Node, and also allows to ask for
        the number of nodes in the group using len().
        """
        return convert.ConvertIterator(self._backend_entity.nodes)

    def remove_nodes(self, nodes):
        """
        Remove a node or a set of nodes to the group.

        :note: The group must be already stored.

        :note: each of the nodes passed to add_nodes must be already stored.

        :param nodes: a Node or DbNode object to add to the group, or
          a list of Nodes or DbNodes to add.
        """
        self._backend_entity.remove_nodes(nodes)

    @classmethod
    def get(cls, **kwargs):
        """
        Custom get for group which can be used to get a group with the given attributes

        :param kwargs: the attributes to match the group to
        :return: the group
        :rtype: :class:`aiida.orm.Group`
        """
        from aiida.orm import QueryBuilder

        query = QueryBuilder()
        filters = {}
        for key, val in kwargs.items():
            filters[key] = {'==': val}

        query.append(cls, filters=filters)
        results = query.all()
        if len(results) > 1:
            raise exceptions.MultipleObjectsError("Found {} groups matching criteria '{}'".format(len(results), kwargs))
        if not results:
            raise exceptions.NotExistent("No group found matching criteria '{}'".format(kwargs))
        return results[0][0]

    @classmethod
    def get_or_create(cls, backend=None, **kwargs):
        """
        Try to retrieve a group from the DB with the given arguments;
        create (and store) a new group if such a group was not present yet.

        :return: (group, created) where group is the group (new or existing,
          in any case already stored) and created is a boolean saying
        """
        import warnings
        # pylint: disable=redefined-builtin
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning
        warnings.warn('this method has been deprecated use Group.objects.get_or_create() instead', DeprecationWarning)  # pylint: disable=no-member

        return cls.objects(backend).get_or_create(**kwargs)

    @classmethod
    def get_from_string(cls, string):
        """
        Get a group from a string.
        If only the label is provided, without colons,
        only user-defined groups are searched;
        add ':type_str' after the group label to choose also
        the type of the group equal to 'type_str'
        (e.g. 'data.upf', 'import', etc.)

        :raise ValueError: if the group type does not exist.
        :raise NotExistent: if the group is not found.
        """
        label, sep, typestr = string.rpartition(':')
        if not sep:
            label = typestr
            typestr = GroupTypeString.USER.value

        try:
            internal_type_string = GroupTypeString(typestr).value
        except ValueError:
            msg = ("Invalid group type '{}'. Valid group types are: "
                   "{}".format(typestr, ', '.join([i.value for i in GroupTypeString])))
            raise ValueError(msg)

        try:
            group = cls.get(label=label, type_string=internal_type_string)
            return group
        except exceptions.NotExistent:
            if typestr:
                msg = ("No group of type '{}' with label '{}' " "found.".format(typestr, label))
            else:
                msg = ("No user-defined group with label '{}' " "found.".format(label))

            raise exceptions.NotExistent(msg)

    def is_user_defined(self):
        """
        :return: True if the group is user defined, False otherwise
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

        :return: get schema of the group
        """
        return {
            "description": {
                "display_name": "Description",
                "help_text": "short description of the Computer",
                "is_foreign_key": False,
                "type": "str"
            },
            "id": {
                "display_name": "Id",
                "help_text": "Id of the object",
                "is_foreign_key": False,
                "type": "int"
            },
            "label": {
                "display_name": "Label",
                "help_text": "Name of the object",
                "is_foreign_key": False,
                "type": "str"
            },
            "type_string": {
                "display_name": "Type_string",
                "help_text": "Code type",
                "is_foreign_key": False,
                "type": "str"
            },
            "user_id": {
                "display_name": "Id of creator",
                "help_text": "Id of the user that created the node",
                "is_foreign_key": True,
                "related_column": "id",
                "related_resource": "_dbusers",
                "type": "int"
            },
            "uuid": {
                "display_name": "Unique ID",
                "help_text": "Universally Unique Identifier",
                "is_foreign_key": False,
                "type": "unicode"
            }
        }
