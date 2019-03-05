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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import logging

import six

from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy.models.group import DbGroup, table_groups_nodes
from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.common.exceptions import UniquenessError
from aiida.common.lang import type_check
from aiida.orm.implementation.groups import BackendGroup, BackendGroupCollection
from . import entities
from . import users
from . import utils

__all__ = ('SqlaGroup', 'SqlaGroupCollection')

_LOGGER = logging.getLogger(__name__)


# Unfortunately the linter doesn't seem to be able to pick up on the fact that the abstract property 'id'
# of BackendGroup is actually implemented in SqlaModelEntity so disable the abstract check
class SqlaGroup(entities.SqlaModelEntity[DbGroup], BackendGroup):  # pylint: disable=abstract-method
    """The SQLAlchemy Group object"""

    MODEL_CLASS = DbGroup

    def __init__(self, backend, label, user, description='', type_string=''):
        """
        Construct a new SQLA group

        :param backend: the backend to use
        :param label: the group label
        :param user: the owner of the group
        :param description: an optional group description
        :param type_string: an optional type for the group to contain
        """
        type_check(user, users.SqlaUser)
        super(SqlaGroup, self).__init__(backend)

        dbgroup = DbGroup(label=label, description=description, user=user.dbmodel, type_string=type_string)
        self._dbmodel = utils.ModelWrapper(dbgroup)

    @property
    def label(self):
        return self._dbmodel.label

    @label.setter
    def label(self, label):
        """
        Attempt to change the label of the group instance. If the group is already stored
        and the another group of the same type already exists with the desired label, a
        UniquenessError will be raised

        :param label: the new group label
        :raises aiida.common.UniquenessError: if another group of same type and label already exists
        """
        self._dbmodel.label = label

        if self.is_stored:
            try:
                self._dbmodel.save()
            except Exception:
                raise UniquenessError('a group of the same type with the label {} already exists'.format(label))

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
        return self._dbmodel.type_string

    @property
    def user(self):
        return self._backend.users.from_dbmodel(self._dbmodel.user)

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

    def count(self):
        """Return the number of entities in this group.

        :return: integer number of entities contained within the group
        """
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()
        return session.query(self.MODEL_CLASS).join(self.MODEL_CLASS.dbnodes).filter(DbGroup.id == self.pk).count()

    @property
    def nodes(self):
        """Get an iterator to all the nodes in the group"""

        class Iterator(object):  # pylint: disable=useless-object-inheritance
            """Nodes iterator"""

            def __init__(self, dbnodes, backend):
                self._backend = backend
                self._dbnodes = dbnodes
                self._iter = dbnodes.__iter__()
                self.generator = self._genfunction()

            def _genfunction(self):
                for node in self._iter:
                    yield self._backend.get_backend_entity(node)

            def __iter__(self):
                return self

            def __len__(self):
                return self._dbnodes.count()

            def __getitem__(self, value):
                if isinstance(value, slice):
                    return [self._backend.get_backend_entity(n) for n in self._dbnodes[value]]

                return self._backend.get_backend_entity(self._dbnodes[value])

            # For future python-3 compatibility
            def __next__(self):
                return next(self.generator)

            def next(self):
                return next(self.generator)

        return Iterator(self._dbmodel.dbnodes, self._backend)

    def add_nodes(self, nodes, **kwargs):
        """Add a node or a set of nodes to the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a list of `BackendNode` instance to be added to this group

        :param kwargs:
            skip_orm: When the flag is on, the SQLA ORM is skipped and SQLA is used
            to create a direct SQL INSERT statement to the group-node relationship
            table (to improve speed).
        """
        from sqlalchemy.exc import IntegrityError  # pylint: disable=import-error, no-name-in-module
        from sqlalchemy.dialects.postgresql import insert  # pylint: disable=import-error, no-name-in-module
        from aiida.orm.implementation.sqlalchemy.nodes import SqlaNode
        from aiida.backends.sqlalchemy import get_scoped_session
        from aiida.backends.sqlalchemy.models.base import Base

        super(SqlaGroup, self).add_nodes(nodes)
        skip_orm = kwargs.get('skip_orm', False)

        def check_node(given_node):
            """ Check if given node is of correct type and stored """
            if not isinstance(given_node, SqlaNode):
                raise TypeError('invalid type {}, has to be {}'.format(type(given_node), SqlaNode))

            if not given_node.is_stored:
                raise ValueError('At least one of the provided nodes is unstored, stopping...')

        with utils.disable_expire_on_commit(get_scoped_session()) as session:
            if not skip_orm:
                # Get dbnodes here ONCE, otherwise each call to dbnodes will re-read the current value in the database
                dbnodes = self._dbmodel.dbnodes

                for node in nodes:
                    check_node(node)

                    # Use pattern as suggested here:
                    # http://docs.sqlalchemy.org/en/latest/orm/session_transaction.html#using-savepoint
                    try:
                        with session.begin_nested():
                            dbnodes.append(node.dbmodel)
                            session.flush()
                    except IntegrityError:
                        # Duplicate entry, skip
                        pass
            else:
                ins_dict = list()
                for node in nodes:
                    check_node(node)
                    ins_dict.append({'dbnode_id': node.id, 'dbgroup_id': self.id})

                my_table = Base.metadata.tables['db_dbgroup_dbnodes']
                ins = insert(my_table).values(ins_dict)
                session.execute(ins.on_conflict_do_nothing(index_elements=['dbnode_id', 'dbgroup_id']))

            # Commit everything as up till now we've just flushed
            session.commit()

    def remove_nodes(self, nodes):
        """Remove a node or a set of nodes from the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a list of `BackendNode` instance to be added to this group
        """
        from aiida.orm.implementation.sqlalchemy.nodes import SqlaNode

        super(SqlaGroup, self).remove_nodes(nodes)

        # Get dbnodes here ONCE, otherwise each call to dbnodes will re-read the current value in the database
        dbnodes = self._dbmodel.dbnodes

        list_nodes = []

        for node in nodes:
            if not isinstance(node, SqlaNode):
                raise TypeError('invalid type {}, has to be {}'.format(type(node), SqlaNode))

            if node.id is None:
                raise ValueError('At least one of the provided nodes is unstored, stopping...')

            # If we don't check first, SqlA might issue a DELETE statement for an unexisting key, resulting in an error
            if node.dbmodel in dbnodes:
                list_nodes.append(node.dbmodel)

        for node in list_nodes:
            dbnodes.remove(node)

        sa.get_scoped_session().commit()


class SqlaGroupCollection(BackendGroupCollection):
    """The SLQA collection of groups"""

    ENTITY_CLASS = SqlaGroup

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
              **kwargs):  # pylint: disable=too-many-arguments
        # pylint: disable=too-many-branches
        from aiida.orm.implementation.sqlalchemy.nodes import SqlaNode

        session = sa.get_scoped_session()

        filters = []

        if label is not None:
            filters.append(DbGroup.label == label)
        if type_string is not None:
            filters.append(DbGroup.type_string == type_string)
        if pk is not None:
            filters.append(DbGroup.id == pk)
        if uuid is not None:
            filters.append(DbGroup.uuid == uuid)
        if past_days is not None:
            filters.append(DbGroup.time >= past_days)
        if nodes:
            if not isinstance(nodes, collections.Iterable):
                nodes = [nodes]

            if not all(isinstance(n, (SqlaNode, DbNode)) for n in nodes):
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

        if label_filters:
            for key, value in label_filters.items():
                if not value:
                    continue
                if key == "startswith":
                    filters.append(DbGroup.label.like("{}%".format(value)))
                elif key == "endswith":
                    filters.append(DbGroup.label.like("%{}".format(value)))
                elif key == "contains":
                    filters.append(DbGroup.label.like("%{}%".format(value)))

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
