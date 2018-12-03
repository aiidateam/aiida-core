# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Django Group entity"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import collections
import six

# pylint: disable=no-name-in-module, import-error
from django.db import transaction
from django.db.models import Q

from aiida.orm.implementation.groups import BackendGroup, BackendGroupCollection
from aiida.common.utils import type_check
from aiida.common.exceptions import ModificationNotAllowed
from aiida.backends.djsite.db import models
from .node import Node
from . import entities
from . import users
from . import utils

__all__ = 'DjangoGroup', 'DjangoGroupCollection'


class DjangoGroup(entities.DjangoModelEntity[models.DbGroup], BackendGroup):  # pylint: disable=abstract-method
    """The Django group object"""
    MODEL_CLASS = models.DbGroup

    def __init__(self, backend, name, user, description='', type_string=''):
        """Construct a new Django group"""
        type_check(user, users.DjangoUser)
        super(DjangoGroup, self).__init__(backend)

        self._dbmodel = utils.ModelWrapper(
            models.DbGroup(name=name, description=description, user=user.dbmodel, type=type_string))

    @property
    def name(self):
        return self._dbmodel.name

    @name.setter
    def name(self, name):
        """
        Attempt to change the name of the group instance. If the group is already stored
        and the another group of the same type already exists with the desired name, a
        UniquenessError will be raised

        :param name: the new group name
        :raises UniquenessError: if another group of same type and name already exists
        """
        self._dbmodel.name = name

    @property
    def description(self):
        return self._dbmodel.description

    @description.setter
    def description(self, value):
        self._dbmodel.description = value

    @property
    def type_string(self):
        return self._dbmodel.type

    @property
    def user(self):
        return self._backend.users.from_dbmodel(self._dbmodel.user)

    @user.setter
    def user(self, new_user):
        type_check(new_user, users.DjangoUser)
        assert new_user.backend == self.backend, "User from a different backend"
        self._dbmodel.user = new_user.dbmodel

    @property
    def uuid(self):
        return six.text_type(self._dbmodel.uuid)

    def __int__(self):
        if not self.is_stored:
            return None

        return self._dbnode.pk

    def store(self):
        if not self.is_stored:
            with transaction.atomic():
                if self.user is not None and not self.user.is_stored:
                    self.user.store()
                    # We now have to reset the model's user entry because
                    # django will have assigned the user an ID but this
                    # is not automatically propagated to us
                    self._dbmodel.user = self.user.dbmodel
                self._dbmodel.save()

        # To allow to do directly g = Group(...).store()
        return self

    def add_nodes(self, nodes):
        from aiida.backends.djsite.db.models import DbNode
        if not self.is_stored:
            raise ModificationNotAllowed("Cannot add nodes to a group before " "storing")

        # First convert to a list
        if isinstance(nodes, (Node, DbNode)):
            nodes = [nodes]

        if isinstance(nodes, six.string_types) or not isinstance(nodes, collections.Iterable):
            raise TypeError("Invalid type passed as the 'nodes' parameter to "
                            "add_nodes, can only be a Node, DbNode, or a list "
                            "of such objects, it is instead {}".format(str(type(nodes))))

        list_pk = []
        for node in nodes:
            if not isinstance(node, (Node, DbNode)):
                raise TypeError("Invalid type of one of the elements passed "
                                "to add_nodes, it should be either a Node or "
                                "a DbNode, it is instead {}".format(str(type(node))))
            if node.pk is None:
                raise ValueError("At least one of the provided nodes is " "unstored, stopping...")
            list_pk.append(node.pk)

        self._dbmodel.dbnodes.add(*list_pk)

    @property
    def nodes(self):
        """Get an iterator to the nodes in the group"""

        class Iterator(object):
            """The nodes iterator"""

            def __init__(self, dbnodes):
                self.dbnodes = dbnodes
                self.generator = self._genfunction()

            def _genfunction(self):
                for node in self.dbnodes:
                    yield node.get_aiida_class()

            def __iter__(self):
                return self

            def __len__(self):
                return self.dbnodes.count()

            # For future python-3 compatibility
            def __next__(self):
                return next(self.generator)

            def next(self):
                return next(self.generator)

        return Iterator(self._dbmodel.dbnodes.all())

    def remove_nodes(self, nodes):
        from aiida.backends.djsite.db.models import DbNode
        if not self.is_stored:
            raise ModificationNotAllowed("Cannot remove nodes from a group " "before storing")

        # First convert to a list
        if isinstance(nodes, (Node, DbNode)):
            nodes = [nodes]

        if isinstance(nodes, six.string_types) or not isinstance(nodes, collections.Iterable):
            raise TypeError("Invalid type passed as the 'nodes' parameter to "
                            "remove_nodes, can only be a Node, DbNode, or a "
                            "list of such objects, it is instead {}".format(str(type(nodes))))

        list_pk = []
        for node in nodes:
            if not isinstance(node, (Node, DbNode)):
                raise TypeError("Invalid type of one of the elements passed "
                                "to add_nodes, it should be either a Node or "
                                "a DbNode, it is instead {}".format(str(type(node))))
            if node.pk is None:
                raise ValueError("At least one of the provided nodes is " "unstored, stopping...")
            list_pk.append(node.pk)

        self._dbmodel.dbnodes.remove(*list_pk)


class DjangoGroupCollection(BackendGroupCollection):
    """The Django Group collection"""

    ENTITY_CLASS = DjangoGroup

    def query(self,
              name=None,
              type_string=None,
              pk=None,
              uuid=None,
              nodes=None,
              user=None,
              node_attributes=None,
              past_days=None,
              name_filters=None,
              **kwargs):  # pylint: disable=too-many-arguments
        # pylint: disable=too-many-branches,too-many-locals
        # Analyze args and kwargs to create the query
        queryobject = Q()
        if name is not None:
            queryobject &= Q(name=name)

        if type_string is not None:
            queryobject &= Q(type=type_string)

        if pk is not None:
            queryobject &= Q(pk=pk)

        if uuid is not None:
            queryobject &= Q(uuid=uuid)

        if past_days is not None:
            queryobject &= Q(time__gte=past_days)

        if nodes is not None:
            pk_list = []

            if not isinstance(nodes, collections.Iterable):
                nodes = [nodes]

            for node in nodes:
                if not isinstance(node, (Node, models.DbNode)):
                    raise TypeError("At least one of the elements passed as "
                                    "nodes for the query on Group is neither "
                                    "a Node nor a DbNode")
                pk_list.append(node.pk)

            queryobject &= Q(dbnodes__in=pk_list)

        if user is not None:
            if isinstance(user, six.string_types):
                queryobject &= Q(user__email=user)
            else:
                queryobject &= Q(user=user.id)

        if name_filters is not None:
            name_filters_list = {"name__" + key: value for (key, value) in name_filters.items() if value}
            queryobject &= Q(**name_filters_list)

        groups_pk = set(models.DbGroup.objects.filter(queryobject, **kwargs).values_list('pk', flat=True))

        if node_attributes is not None:
            for k, vlist in node_attributes.items():
                if isinstance(vlist, six.string_types) or not isinstance(vlist, collections.Iterable):
                    vlist = [vlist]

                for value in vlist:
                    # This will be a dictionary of the type
                    # {'datatype': 'txt', 'tval': 'xxx') for instance, if
                    # the passed data is a string
                    base_query_dict = models.DbAttribute.get_query_dict(value)
                    # prepend to the key the right django string to SQL-join
                    # on the right table
                    query_dict = {'dbnodes__dbattributes__{}'.format(k2): v2 for k2, v2 in base_query_dict.items()}

                    # I narrow down the list of groups.
                    # I had to do it in this way, with multiple DB hits and
                    # not a single, complicated query because in SQLite
                    # there is a maximum of 64 tables in a join.
                    # Since typically one requires a small number of filters,
                    # this should be ok.
                    groups_pk = groups_pk.intersection(
                        models.DbGroup.objects.filter(pk__in=groups_pk, dbnodes__dbattributes__key=k,
                                                      **query_dict).values_list('pk', flat=True))

        retlist = []
        # Return sorted by pk
        for dbgroup in sorted(groups_pk):
            retlist.append(DjangoGroup.from_dbmodel(models.DbGroup.objects.get(id=dbgroup), self._backend))

        return retlist

    def delete(self, id):  # pylint: disable=redefined-builtin
        models.DbGroup.objects.filter(id=id).delete()
