# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQLA groups"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import collections
import logging
import six

from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy.models.group import DbGroup, table_groups_nodes
from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.common.exceptions import (ModificationNotAllowed, UniquenessError)
from aiida.common.utils import type_check
from aiida.orm.implementation.groups import BackendGroup, BackendGroupCollection

from . import entities
from . import users
from . import utils

__all__ = 'SqlaGroup', 'SqlaGroupCollection'

_LOGGER = logging.getLogger(__name__)


# Unfortunately the linter doesn't seem to be able to pick up on the fact that the abstract property 'id'
# of BackendGroup is actually implemented in SqlaModelEntity so disable the abstract check
class SqlaGroup(entities.SqlaModelEntity[DbGroup], BackendGroup):  # pylint: disable=abstract-method
    """The SQLAlchemy Group object"""

    MODEL_CLASS = DbGroup

    def __init__(self, backend, name, user, description='', type_string=''):
        """
        Construct a new SQLA group

        :param backend: the backend to use
        :param name: the group name
        :param user: the owner of the group
        :param description: an optional group description
        :param type_string: an optional type for the group to contain
        """
        type_check(user, users.SqlaUser)
        super(SqlaGroup, self).__init__(backend)

        dbgroup = DbGroup(name=name, description=description, user=user.dbmodel, type=type_string)
        self._dbmodel = utils.ModelWrapper(dbgroup)

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

        if self.is_stored:
            try:
                self._dbmodel.save()
            except Exception:
                raise UniquenessError('a group of the same type with the name {} already exists'.format(name))

    @property
    def description(self):
        return self._dbmodel.description

    @description.setter
    def description(self, value):
        self._dbmodel.description = value

        # Update the entry in the DB, if the group is already stored
        if self.is_stored:
            self._dbmodel.save()

    @property
    def type_string(self):
        return self._dbmodel.type

    @property
    def user(self):
        return self._dbmodel.user.get_aiida_class()

    @user.setter
    def user(self, new_user):
        type_check(new_user, users.SqlaUser)
        self._dbmodel.user = new_user.dbmodel

    @property
    def pk(self):
        return self._dbmodel.id

    @property
    def uuid(self):
        return six.text_type(self._dbmodel.uuid)

    def __int__(self):
        if not self.is_stored:
            return None

        return self._dbnode.id

    @property
    def is_stored(self):
        return self.pk is not None

    def store(self):
        self._dbmodel.save()
        return self

    def add_nodes(self, nodes):
        from sqlalchemy.exc import IntegrityError  # pylint: disable=import-error, no-name-in-module

        if not self.is_stored:
            raise ModificationNotAllowed("Cannot add nodes to a group before " "storing")
        from aiida.orm.implementation.sqlalchemy.node import Node
        from aiida.backends.sqlalchemy import get_scoped_session

        # First convert to a list
        if isinstance(nodes, (Node, DbNode)):
            nodes = [nodes]

        if isinstance(nodes, six.string_types) or not isinstance(nodes, collections.Iterable):
            raise TypeError("Invalid type passed as the 'nodes' parameter to "
                            "add_nodes, can only be a Node, DbNode, or a list "
                            "of such objects, it is instead {}".format(str(type(nodes))))

        with utils.disable_expire_on_commit(get_scoped_session()) as session:
            # Get dbnodes here ONCE, otherwise each call to _dbgroup.dbnodes will
            # re-read the current value in the database
            dbnodes = self._dbmodel.dbnodes
            for node in nodes:
                if not isinstance(node, (Node, DbNode)):
                    raise TypeError("Invalid type of one of the elements passed "
                                    "to add_nodes, it should be either a Node or "
                                    "a DbNode, it is instead {}".format(str(type(node))))

                if node.id is None:
                    raise ValueError("At least one of the provided nodes is " "unstored, stopping...")
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
        """Get an iterator to all the nodes in the group"""

        class Iterator(object):
            """Nodes iterator"""

            def __init__(self, dbnodes):
                self._dbnodes = dbnodes
                self._iter = dbnodes.__iter__()
                self.generator = self._genfunction()

            def _genfunction(self):
                for node in self._iter:
                    yield node.get_aiida_class()

            def __iter__(self):
                return self

            def __len__(self):
                return self._dbnodes.count()

            # For future python-3 compatibility
            def __next__(self):
                return next(self.generator)

            def next(self):
                return next(self.generator)

        return Iterator(self._dbmodel.dbnodes)

    def remove_nodes(self, nodes):
        """
        Remove the given nodes from the group.  Can pass a single node or a collection of nodes

        :param nodes: the nodes to remove
        """
        if not self.is_stored:
            raise ModificationNotAllowed("Cannot remove nodes from a group " "before storing")

        from aiida.orm.implementation.sqlalchemy.node import Node
        # First convert to a list
        if isinstance(nodes, (Node, DbNode)):
            nodes = [nodes]

        if isinstance(nodes, six.string_types) or not isinstance(nodes, collections.Iterable):
            raise TypeError("Invalid type passed as the 'nodes' parameter to "
                            "remove_nodes, can only be a Node, DbNode, or a "
                            "list of such objects, it is instead {}".format(str(type(nodes))))

        list_nodes = []
        # Have to save dbndoes here ONCE, otherwise it will be reloaded from
        # the database each time we access it through _dbgroup.dbnodes
        dbnodes = self._dbmodel.dbnodes
        for node in nodes:
            if not isinstance(node, (Node, DbNode)):
                raise TypeError("Invalid type of one of the elements passed "
                                "to add_nodes, it should be either a Node or "
                                "a DbNode, it is instead {}".format(str(type(node))))
            if node.id is None:
                raise ValueError("At least one of the provided nodes is " "unstored, stopping...")
            if isinstance(node, Node):
                node = node.dbnode
            # If we don't check first, SqlA might issue a DELETE statement for
            # an unexisting key, resulting in an error
            if node in dbnodes:
                list_nodes.append(node)

        for node in list_nodes:
            dbnodes.remove(node)

        sa.get_scoped_session().commit()


class SqlaGroupCollection(BackendGroupCollection):
    """The SLQA collection of groups"""

    ENTITY_CLASS = SqlaGroup

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
        # pylint: disable=too-many-branches
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
                table_groups_nodes.c["dbnode_id"].in_([n.id for n in nodes]),
                table_groups_nodes.c["dbgroup_id"] == DbGroup.id).exists())

            filters.append(sub_query)
        if user:
            if isinstance(user, six.string_types):
                filters.append(DbGroup.user.has(email=user.email))
            else:
                type_check(user, users.SqlaUser)
                filters.append(DbGroup.user == user.dbmodel)

        if name_filters:
            for key, value in name_filters.items():
                if not value:
                    continue
                if key == "startswith":
                    filters.append(DbGroup.name.like("{}%".format(value)))
                elif key == "endswith":
                    filters.append(DbGroup.name.like("%{}".format(value)))
                elif key == "contains":
                    filters.append(DbGroup.name.like("%{}%".format(value)))

        if node_attributes:
            _LOGGER.warning("SQLA query doesn't support node attribute filters, ignoring '%s'", node_attributes)

        if kwargs:
            _LOGGER.warning("SQLA query doesn't support additional filters, ignoring '%s'", kwargs)
        groups = (session.query(DbGroup).filter(*filters).order_by(DbGroup.id).distinct().all())

        return [SqlaGroup.from_dbmodel(group, self._backend) for group in groups]

    def delete(self, id):  # pylint: disable=redefined-builtin
        session = sa.get_scoped_session()

        session.query(DbGroup).get(id).delete()
        session.commit()
