# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import collections
from copy import copy

import six
from sqlalchemy.orm.session import make_transient

from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy.models.group import DbGroup, table_groups_nodes
from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.common.exceptions import (ModificationNotAllowed, UniquenessError, NotExistent)
from aiida.common.utils import type_check
from aiida.orm.implementation.general.group import AbstractGroup

from . import user as users
from . import utils


class Group(AbstractGroup):
    def __init__(self, **kwargs):
        from aiida.orm.backends import construct_backend
        super(Group, self).__init__()

        self._backend = construct_backend()

        given_dbgroup = kwargs.pop('dbgroup', None)

        if given_dbgroup is not None:

            # Check that there is no other parameter passed besides dbgroup
            if kwargs:
                raise ValueError("If you pass a dbgroups, you cannot pass any "
                                 "further parameter")

            if isinstance(given_dbgroup, six.integer_types):
                dbgroup_res = DbGroup.query.filter_by(id=given_dbgroup).first()
                if not dbgroup_res:
                    raise NotExistent("Group with pk={} does not exist".format(
                        given_dbgroup))
                dbgroup = dbgroup_res
            elif isinstance(given_dbgroup, DbGroup):
                dbgroup = given_dbgroup
            else:
                raise ValueError("Unrecognised inputs '{}'".format(kwargs))
        else:
            name = kwargs.pop('name', None)
            if name is None:
                raise ValueError("You have to specify a group name")
            group_type = kwargs.pop('type_string',
                                    "")  # By default, an user group

            # Get the user and extract the dbuser instance
            user = kwargs.pop('user', self._backend.users.get_automatic_user())
            user = user.dbuser

            description = kwargs.pop('description', "")

            if kwargs:
                raise ValueError("Too many parameters passed to Group, the "
                                 "unknown parameters are: {}".format(", ".join(kwargs.keys())))

            dbgroup = DbGroup(name=name, description=description,
                              user=user, type=group_type)

        self._dbgroup = utils.ModelWrapper(dbgroup)

    @property
    def name(self):
        return self._dbgroup.name

    @name.setter
    def name(self, name):
        """
        Attempt to change the name of the group instance. If the group is already stored
        and the another group of the same type already exists with the desired name, a
        UniquenessError will be raised

        :param name: the new group name
        :raises UniquenessError: if another group of same type and name already exists
        """
        self._dbgroup.name = name

        if self.is_stored:
            try:
                self._dbgroup.save()
            except Exception:
                raise UniquenessError('a group of the same type with the name {} already exists'.format(name))

    @property
    def description(self):
        return self._dbgroup.description

    @description.setter
    def description(self, value):
        self._dbgroup.description = value

        # Update the entry in the DB, if the group is already stored
        if self.is_stored:
            self._dbgroup.save()

    @property
    def type_string(self):
        return self._dbgroup.type

    @property
    def user(self):
        return self._dbgroup.user.get_aiida_class()

    @user.setter
    def user(self, new_user):
        type_check(new_user, users.SqlaUser)
        self._dbgroup.user = new_user.dbuser

    @property
    def dbgroup(self):
        return self._dbgroup._model

    @property
    def pk(self):
        return self._dbgroup.id

    @property
    def id(self):
        return self._dbgroup.id

    @property
    def uuid(self):
        return six.text_type(self._dbgroup.uuid)

    def __int__(self):
        if not self.is_stored:
            return None
        else:
            return self._dbnode.id

    @property
    def is_stored(self):
        return self.pk is not None

    def store(self):
        self._dbgroup.save()
        return self

    def add_nodes(self, nodes):
        from sqlalchemy.exc import IntegrityError

        if not self.is_stored:
            raise ModificationNotAllowed("Cannot add nodes to a group before "
                                         "storing")
        from aiida.orm.implementation.sqlalchemy.node import Node
        from aiida.backends.sqlalchemy import get_scoped_session

        # First convert to a list
        if isinstance(nodes, (Node, DbNode)):
            nodes = [nodes]

        if isinstance(nodes, six.string_types) or not isinstance(
                nodes, collections.Iterable):
            raise TypeError("Invalid type passed as the 'nodes' parameter to "
                            "add_nodes, can only be a Node, DbNode, or a list "
                            "of such objects, it is instead {}".format(
                str(type(nodes))))

        with utils.disable_expire_on_commit(get_scoped_session()) as session:
            # Get dbnodes here ONCE, otherwise each call to _dbgroup.dbnodes will
            # re-read the current value in the database
            dbnodes = self._dbgroup.dbnodes
            for node in nodes:
                if not isinstance(node, (Node, DbNode)):
                    raise TypeError("Invalid type of one of the elements passed "
                                    "to add_nodes, it should be either a Node or "
                                    "a DbNode, it is instead {}".format(
                        str(type(node))))

                if node.id is None:
                    raise ValueError("At least one of the provided nodes is "
                                     "unstored, stopping...")
                if isinstance(node, Node):
                    to_add = node.dbnode
                else:
                    to_add = node

                # Use pattern as suggested here:
                # http://docs.sqlalchemy.org/en/latest/orm/session_transaction.html#using-savepoint
                try:
                    with session.begin_nested():
                        dbnodes.append(to_add)
                        session.flush()
                except IntegrityError:
                    # Duplicate entry, skip
                    pass

            # Commit everything as up till now we've just flushed
            session.commit()

    @property
    def nodes(self):
        class iterator(object):
            def __init__(self, dbnodes):
                self._dbnodes = dbnodes
                self._iter = dbnodes.__iter__()
                self.generator = self._genfunction()

            def _genfunction(self):
                for n in self._iter:
                    yield n.get_aiida_class()

            def __iter__(self):
                return self

            def __len__(self):
                return self._dbnodes.count()

            # For future python-3 compatibility
            def __next__(self):
                return next(self.generator)

            def next(self):
                return next(self.generator)

        return iterator(self._dbgroup.dbnodes)

    def remove_nodes(self, nodes):
        if not self.is_stored:
            raise ModificationNotAllowed("Cannot remove nodes from a group "
                                         "before storing")

        from aiida.orm.implementation.sqlalchemy.node import Node
        # First convert to a list
        if isinstance(nodes, (Node, DbNode)):
            nodes = [nodes]

        if isinstance(nodes, six.string_types) or not isinstance(
                nodes, collections.Iterable):
            raise TypeError("Invalid type passed as the 'nodes' parameter to "
                            "remove_nodes, can only be a Node, DbNode, or a "
                            "list of such objects, it is instead {}".format(str(type(nodes))))

        list_nodes = []
        # Have to save dbndoes here ONCE, otherwise it will be reloaded from
        # the database each time we access it through _dbgroup.dbnodes
        dbnodes = self._dbgroup.dbnodes
        for node in nodes:
            if not isinstance(node, (Node, DbNode)):
                raise TypeError("Invalid type of one of the elements passed "
                                "to add_nodes, it should be either a Node or "
                                "a DbNode, it is instead {}".format(
                    str(type(node))))
            if node.id is None:
                raise ValueError("At least one of the provided nodes is "
                                 "unstored, stopping...")
            if isinstance(node, Node):
                node = node.dbnode
            # If we don't check first, SqlA might issue a DELETE statement for
            # an unexisting key, resulting in an error
            if node in dbnodes:
                list_nodes.append(node)

        for node in list_nodes:
            dbnodes.remove(node)

        sa.get_scoped_session().commit()

    @classmethod
    def query(cls, name=None, type_string="", pk=None, uuid=None, nodes=None,
              user=None, node_attributes=None, past_days=None,
              name_filters=None, **kwargs):
        from aiida.orm.implementation.sqlalchemy.node import Node

        session = sa.get_scoped_session()

        filters = []

        if name is not None:
            filters.append(DbGroup.name == name)
        if type_string is not None:
            filters.append(DbGroup.type == type_string)
        if pk is not None:
            filters.append(DbGroup.id == pk)
        if uuid is not None:
            filters.append(DbGroup.uuid == uuid)
        if past_days is not None:
            filters.append(DbGroup.time >= past_days)
        if nodes:
            if not isinstance(nodes, collections.Iterable):
                nodes = [nodes]

            if not all(isinstance(n, (Node, DbNode)) for n in nodes):
                raise TypeError("At least one of the elements passed as "
                                "nodes for the query on Group is neither "
                                "a Node nor a DbNode")

            # In the case of the Node orm from Sqlalchemy, there is an id
            # property on it.
            sub_query = (session.query(table_groups_nodes).filter(
                table_groups_nodes.c["dbnode_id"].in_(
                    [n.id for n in nodes]),
                table_groups_nodes.c["dbgroup_id"] == DbGroup.id
            ).exists())

            filters.append(sub_query)
        if user:
            if isinstance(user, six.string_types):
                filters.append(DbGroup.user.has(email=user))
            else:
                # This should be a DbUser
                filters.append(DbGroup.user == user.dbuser)

        if name_filters:
            for (k, v) in name_filters.items():
                if not v:
                    continue
                if k == "startswith":
                    filters.append(DbGroup.name.like("{}%".format(v)))
                elif k == "endswith":
                    filters.append(DbGroup.name.like("%{}".format(v)))
                elif k == "contains":
                    filters.append(DbGroup.name.like("%{}%".format(v)))

        if node_attributes:
            # TODO SP: IMPLEMENT THIS
            pass

        # TODO SP: handle **kwargs
        groups = (session.query(DbGroup.id).filter(*filters)
                  .order_by(DbGroup.id).distinct().all())

        return [cls(dbgroup=g[0]) for g in groups]

    def delete(self):

        session = sa.get_scoped_session()

        if self.pk is not None:
            session.delete(self._dbgroup)
            session.commit()

            new_group = copy(self._dbgroup)
            make_transient(new_group)
            new_group.id = None
            self._dbgroup = new_group
