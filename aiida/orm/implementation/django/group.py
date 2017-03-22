# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import collections

from aiida.orm.implementation.general.group import AbstractGroup

from aiida.common.exceptions import (ModificationNotAllowed, UniquenessError,
                                     NotExistent)

from aiida.orm.implementation.django.node import Node


from aiida.backends.djsite.utils import get_automatic_user

from django.db import transaction, IntegrityError
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from aiida.orm.implementation.django.utils import get_db_columns




class Group(AbstractGroup):
    def __init__(self, **kwargs):
        from aiida.backends.djsite.db.models import DbGroup
        dbgroup = kwargs.pop('dbgroup', None)

        if dbgroup is not None:
            if isinstance(dbgroup, (int, long)):
                try:
                    dbgroup = DbGroup.objects.get(pk=dbgroup)
                except ObjectDoesNotExist:
                    raise NotExistent("Group with pk={} does not exist".format(
                        dbgroup))
            if not isinstance(dbgroup, DbGroup):
                raise TypeError("dbgroup is not a DbGroup instance, it is "
                                "instead {}".format(str(type(dbgroup))))
            if kwargs:
                raise ValueError("If you pass a dbgroups, you cannot pass any "
                                 "further parameter")

            self._dbgroup = dbgroup
        else:
            name = kwargs.pop('name', None)
            if name is None:
                raise ValueError("You have to specify a group name")
            group_type = kwargs.pop('type_string',
                                    "")  # By default, an user group
            user = kwargs.pop('user', get_automatic_user())
            description = kwargs.pop('description', "")
            self._dbgroup = DbGroup(name=name, description=description,
                                    user=user, type=group_type)
            if kwargs:
                raise ValueError("Too many parameters passed to Group, the "
                                 "unknown parameters are: {}".format(
                    ", ".join(kwargs.keys())))

    @staticmethod
    def get_db_columns():
        from aiida.backends.djsite.db.models import DbGroup
        return get_db_columns(DbGroup)

    @property
    def name(self):
        return self.dbgroup.name

    @property
    def description(self):
        return self.dbgroup.description

    @description.setter
    def description(self, value):
        self.dbgroup.description = value

        # Update the entry in the DB, if the group is already stored
        if self.is_stored:
            self.dbgroup.save()

    @property
    def type_string(self):
        return self.dbgroup.type

    @property
    def user(self):
        return self.dbgroup.user

    @property
    def dbgroup(self):
        return self._dbgroup

    @property
    def pk(self):
        return self._dbgroup.pk

    @property
    def id(self):
        return self._dbgroup.pk

    @property
    def uuid(self):
        return unicode(self.dbgroup.uuid)

    def __int__(self):
        if self._to_be_stored:
            return None
        else:
            return self._dbnode.pk

    @property
    def is_stored(self):
        return self.pk is not None

    def store(self):
        if not self.is_stored:
            try:
                with transaction.atomic():
                    self.dbgroup.save()
            except IntegrityError:
                raise UniquenessError("A group with the same name (and of the "
                                      "same type) already "
                                      "exists, unable to store")

        # To allow to do directly g = Group(...).store()
        return self

    def add_nodes(self, nodes):
        from aiida.backends.djsite.db.models import DbNode
        if not self.is_stored:
            raise ModificationNotAllowed("Cannot add nodes to a group before "
                                         "storing")

        # First convert to a list
        if isinstance(nodes, (Node, DbNode)):
            nodes = [nodes]

        if isinstance(nodes, basestring) or not isinstance(
                nodes, collections.Iterable):
            raise TypeError("Invalid type passed as the 'nodes' parameter to "
                            "add_nodes, can only be a Node, DbNode, or a list "
                            "of such objects, it is instead {}".format(
                str(type(nodes))))

        list_pk = []
        for node in nodes:
            if not isinstance(node, (Node, DbNode)):
                raise TypeError("Invalid type of one of the elements passed "
                                "to add_nodes, it should be either a Node or "
                                "a DbNode, it is instead {}".format(
                    str(type(node))))
            if node.pk is None:
                raise ValueError("At least one of the provided nodes is "
                                 "unstored, stopping...")
            list_pk.append(node.pk)

        self.dbgroup.dbnodes.add(*list_pk)

    @property
    def nodes(self):
        class iterator(object):
            def __init__(self, dbnodes):
                self.dbnodes = dbnodes
                self.generator = self._genfunction()

            def _genfunction(self):
                for n in self.dbnodes:
                    yield n.get_aiida_class()

            def __iter__(self):
                return self

            def __len__(self):
                return self.dbnodes.count()

            # For future python-3 compatibility
            def __next__(self):
                return self.next()

            def next(self):
                return next(self.generator)

        return iterator(self.dbgroup.dbnodes.all())

    def remove_nodes(self, nodes):
        from aiida.backends.djsite.db.models import DbNode
        if not self.is_stored:
            raise ModificationNotAllowed("Cannot remove nodes from a group "
                                         "before storing")

        # First convert to a list
        if isinstance(nodes, (Node, DbNode)):
            nodes = [nodes]

        if isinstance(nodes, basestring) or not isinstance(
                nodes, collections.Iterable):
            raise TypeError("Invalid type passed as the 'nodes' parameter to "
                            "remove_nodes, can only be a Node, DbNode, or a "
                            "list of such objects, it is instead {}".format(
                str(type(nodes))))

        list_pk = []
        for node in nodes:
            if not isinstance(node, (Node, DbNode)):
                raise TypeError("Invalid type of one of the elements passed "
                                "to add_nodes, it should be either a Node or "
                                "a DbNode, it is instead {}".format(
                    str(type(node))))
            if node.pk is None:
                raise ValueError("At least one of the provided nodes is "
                                 "unstored, stopping...")
            list_pk.append(node.pk)

        self.dbgroup.dbnodes.remove(*list_pk)

    @classmethod
    def query(cls, name=None, type_string="", pk=None, uuid=None, nodes=None,
              user=None, node_attributes=None, past_days=None,
              name_filters=None, **kwargs):

        from aiida.backends.djsite.db.models import (DbGroup, DbNode,
                                                     DbAttribute)

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
                if not isinstance(node, (Node, DbNode)):
                    raise TypeError("At least one of the elements passed as "
                                    "nodes for the query on Group is neither "
                                    "a Node nor a DbNode")
                pk_list.append(node.pk)

            queryobject &= Q(dbnodes__in=pk_list)

        if user is not None:
            if isinstance(user, basestring):
                queryobject &= Q(user__email=user)
            else:
                queryobject &= Q(user=user)

        if name_filters is not None:
            name_filters_list = {"name__" + k: v for (k, v)
                                 in name_filters.iteritems() if v}
            queryobject &= Q(**name_filters_list)

        groups_pk = set(DbGroup.objects.filter(
            queryobject, **kwargs).values_list('pk', flat=True))

        if node_attributes is not None:
            for k, vlist in node_attributes.iteritems():
                if isinstance(vlist, basestring) or not isinstance(
                        vlist, collections.Iterable):
                    vlist = [vlist]

                for v in vlist:
                    # This will be a dictionary of the type
                    # {'datatype': 'txt', 'tval': 'xxx') for instance, if
                    # the passed data is a string
                    base_query_dict = DbAttribute.get_query_dict(v)
                    # prepend to the key the right django string to SQL-join
                    # on the right table
                    query_dict = {'dbnodes__dbattributes__{}'.format(k2): v2
                                  for k2, v2 in base_query_dict.iteritems()}

                    # I narrow down the list of groups.
                    # I had to do it in this way, with multiple DB hits and
                    # not a single, complicated query because in SQLite
                    # there is a maximum of 64 tables in a join.
                    # Since typically one requires a small number of filters,
                    # this should be ok.
                    groups_pk = groups_pk.intersection(DbGroup.objects.filter(
                        pk__in=groups_pk, dbnodes__dbattributes__key=k,
                        **query_dict).values_list('pk', flat=True))

        retlist = []
        # Return sorted by pk
        for dbgroup in sorted(groups_pk):
            retlist.append(cls(dbgroup=dbgroup))

        return retlist

    def delete(self):
        if self.pk is not None:
            self.dbgroup.delete()
