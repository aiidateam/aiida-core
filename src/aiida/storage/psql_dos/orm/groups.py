###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQLA groups"""

import logging

from aiida.common.exceptions import UniquenessError
from aiida.common.lang import type_check
from aiida.orm.implementation.groups import BackendGroup, BackendGroupCollection
from aiida.storage.psql_dos.models.group import DbGroup, DbGroupNode

from . import entities, users, utils
from .extras_mixin import ExtrasMixin
from .nodes import SqlaNode

_LOGGER = logging.getLogger(__name__)


# Unfortunately the linter doesn't seem to be able to pick up on the fact that the abstract property 'id'
# of BackendGroup is actually implemented in SqlaModelEntity so disable the abstract check
class SqlaGroup(entities.SqlaModelEntity[DbGroup], ExtrasMixin, BackendGroup):
    """The SQLAlchemy Group object"""

    MODEL_CLASS = DbGroup
    USER_CLASS = users.SqlaUser
    NODE_CLASS = SqlaNode
    GROUP_NODE_CLASS = DbGroupNode

    def __init__(self, backend, label, user, description='', type_string='', time=None):
        """Construct a new SQLA group

        :param backend: the backend to use
        :param label: the group label
        :param user: the owner of the group
        :param description: an optional group description
        :param type_string: an optional type for the group to contain
        """
        type_check(user, self.USER_CLASS)
        super().__init__(backend)

        dbgroup = self.MODEL_CLASS(
            label=label, description=description, user=user.bare_model, type_string=type_string, time=time
        )
        self._model = utils.ModelWrapper(dbgroup, backend)

    @property
    def label(self):
        return self.model.label

    @label.setter
    def label(self, label):
        """Attempt to change the label of the group instance. If the group is already stored
        and the another group of the same type already exists with the desired label, a
        UniquenessError will be raised

        :param label: the new group label
        :raises aiida.common.UniquenessError: if another group of same type and label already exists
        """
        self.model.label = label

        if self.is_stored:
            try:
                self.model.save()
            except Exception:
                raise UniquenessError(f'a group of the same type with the label {label} already exists') from Exception

    @property
    def description(self):
        return self.model.description

    @description.setter
    def description(self, value):
        self.model.description = value

        # Update the entry in the DB, if the group is already stored
        if self.is_stored:
            self.model.save()

    @property
    def type_string(self):
        return self.model.type_string

    @property
    def user(self):
        return self.backend.users.ENTITY_CLASS.from_dbmodel(self.model.user, self.backend)

    @user.setter
    def user(self, new_user):
        type_check(new_user, self.USER_CLASS)
        self.model.user = new_user.bare_model

    @property
    def pk(self):
        return self.model.id

    @property
    def uuid(self):
        return str(self.model.uuid)

    @property
    def time(self):
        return self.model.time

    @property
    def is_stored(self):
        return self.pk is not None

    def store(self):
        self.model.save()
        return self

    def count(self):
        """Return the number of entities in this group.

        :return: integer number of entities contained within the group
        """
        from sqlalchemy.orm import aliased

        group = aliased(self.MODEL_CLASS)
        nodes = aliased(self.GROUP_NODE_CLASS)
        session = self.backend.get_session()
        return session.query(group).join(nodes, nodes.dbgroup_id == group.id).filter(group.id == self.pk).count()

    def clear(self):
        """Remove all the nodes from this group."""
        session = self.backend.get_session()
        # Note we have to call `bare_model` to circumvent flushing data to the database
        self.bare_model.dbnodes = []
        session.commit()

    @property
    def nodes(self):
        """Get an iterator to all the nodes in the group"""

        class Iterator:
            """Nodes iterator"""

            def __init__(self, dbnodes, backend):
                self._backend = backend
                self._dbnodes = dbnodes
                self.generator = self._genfunction()

            def _genfunction(self):
                for node in self._dbnodes:
                    yield self._backend.get_backend_entity(node)

            def __iter__(self):
                return self

            def __len__(self):
                return self._dbnodes.count()

            def __getitem__(self, value):
                if isinstance(value, slice):
                    return [self._backend.get_backend_entity(n) for n in self._dbnodes[value]]

                return self._backend.get_backend_entity(self._dbnodes[value])

            def __next__(self):
                return next(self.generator)

        return Iterator(self.model.dbnodes, self._backend)

    def add_nodes(self, nodes, **kwargs):
        """Add a node or a set of nodes to the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a list of `BackendNode` instance to be added to this group
        """
        from sqlalchemy.dialects.postgresql import insert

        super().add_nodes(nodes)

        def check_node(given_node):
            """Check if given node is of correct type and stored"""
            if not isinstance(given_node, self.NODE_CLASS):
                raise TypeError(f'invalid type {type(given_node)}, has to be {self.NODE_CLASS}')

            if not given_node.is_stored:
                raise ValueError('At least one of the provided nodes is unstored, stopping...')

        with utils.disable_expire_on_commit(self.backend.get_session()) as session:
            ins_dict = []
            for node in nodes:
                check_node(node)
                ins_dict.append({'dbnode_id': node.id, 'dbgroup_id': self.id})
            if len(ins_dict) == 0:
                return

            table = self.GROUP_NODE_CLASS.__table__
            ins = insert(table)
            session.execute(ins.on_conflict_do_nothing(index_elements=['dbnode_id', 'dbgroup_id']), ins_dict)

            # Commit everything as up till now we've just flushed
            if not session.in_nested_transaction():
                session.commit()

    def remove_nodes(self, nodes, **kwargs):
        """Remove a node or a set of nodes from the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a list of `BackendNode` instance to be added to this group
        """
        from sqlalchemy import and_

        super().remove_nodes(nodes)

        def check_node(node):
            if not isinstance(node, self.NODE_CLASS):
                raise TypeError(f'invalid type {type(node)}, has to be {self.NODE_CLASS}')

            if node.id is None:
                raise ValueError('At least one of the provided nodes is unstored, stopping...')

        with utils.disable_expire_on_commit(self.backend.get_session()) as session:
            table = self.GROUP_NODE_CLASS.__table__
            for node in nodes:
                check_node(node)
                clause = and_(table.c.dbnode_id == node.id, table.c.dbgroup_id == self.id)
                statement = table.delete().where(clause)
                session.execute(statement)

            if not session.in_nested_transaction():
                session.commit()


class SqlaGroupCollection(BackendGroupCollection):
    """The SLQA collection of groups"""

    ENTITY_CLASS = SqlaGroup

    def delete(self, id):
        session = self.backend.get_session()

        row = session.get(self.ENTITY_CLASS.MODEL_CLASS, id)
        session.delete(row)
        session.commit()
