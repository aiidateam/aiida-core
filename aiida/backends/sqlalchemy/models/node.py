# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from sqlalchemy import ForeignKey, select, func, join, and_, case
from sqlalchemy.orm import (
    relationship, backref, Query, mapper,
    foreign, aliased
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.schema import Column, UniqueConstraint
from sqlalchemy.types import Integer, String, Boolean, DateTime, Text
# Specific to PGSQL. If needed to be agnostic
# http://docs.sqlalchemy.org/en/rel_0_9/core/custom_types.html?highlight=guid#backend-agnostic-guid-type
# Or maybe rely on sqlalchemy-utils UUID type
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy_utils.types.choice import ChoiceType

from aiida.utils import timezone
from aiida.backends.sqlalchemy.models.base import Base, _QueryProperty, _AiidaQuery
from aiida.backends.sqlalchemy.models.utils import uuid_func

from aiida.common import aiidalogger
from aiida.common.pluginloader import load_plugin
from aiida.common.exceptions import DbContentError, MissingPluginError
from aiida.common.datastructures import calc_states, _sorted_datastates, sort_states


class DbCalcState(Base):
    __tablename__ = "db_dbcalcstate"

    id = Column(Integer, primary_key=True)

    dbnode_id = Column(
        Integer,
        ForeignKey(
            'db_dbnode.id', ondelete="CASCADE",
            deferrable=True, initially="DEFERRED"
        )
    )
    dbnode = relationship(
        'DbNode', backref=backref('dbstates', passive_deletes=True),
    )

    # Note: this is suboptimal: calc_states is not sorted
    # therefore the order is not the expected one. If we
    # were to use the correct order here, we could directly sort
    # without specifying a custom order. This is probably faster,
    # but requires a schema migration at this point
    state = Column(ChoiceType((_, _) for _ in calc_states), index=True)

    time = Column(DateTime(timezone=True), default=timezone.now)

    __table_args__ = (
        UniqueConstraint('dbnode_id', 'state'),
    )


class DbNode(Base):
    __tablename__ = "db_dbnode"

    aiida_query = _QueryProperty(_AiidaQuery)

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid_func)
    type = Column(String(255), index=True)
    label = Column(String(255), index=True, nullable=True,
                   default="")  # Does it make sense to be nullable and have a default?
    description = Column(Text(), nullable=True, default="")
    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now)
    nodeversion = Column(Integer, default=1)
    public = Column(Boolean, default=False)
    attributes = Column(JSONB)
    extras = Column(JSONB)

    dbcomputer_id = Column(
        Integer,
        ForeignKey('db_dbcomputer.id', deferrable=True, initially="DEFERRED", ondelete="RESTRICT"),
        nullable=True
    )

    # This should have the same ondelet behaviour as db_computer_id, right?
    user_id = Column(
        Integer,
        ForeignKey(
            'db_dbuser.id', deferrable=True, initially="DEFERRED", ondelete="restrict"
        ),
        nullable=False
    )

    # TODO SP: The 'passive_deletes=all' argument here means that SQLAlchemy
    # won't take care of automatic deleting in the DbLink table. This still
    # isn't exactly the same behaviour than with Django. The solution to
    # this is probably a ON DELETE inside the DB. On removing node with id=x,
    # we would remove all link with x as an output.

    ######### RELATIONSSHIPS ################

    dbcomputer = relationship(
        'DbComputer',
        backref=backref('dbnodes', passive_deletes='all', cascade='merge')
    )

    # User
    user = relationship(
        'DbUser',
        backref=backref('dbnodes', passive_deletes='all', cascade='merge',)
    )

    # outputs via db_dblink table
    outputs_q = relationship(
        "DbNode", secondary="db_dblink",
        primaryjoin="DbNode.id == DbLink.input_id",
        secondaryjoin="DbNode.id == DbLink.output_id",
        backref=backref("inputs_q", passive_deletes=True, lazy='dynamic'),
        lazy='dynamic',
        passive_deletes=True
    )

    @property
    def outputs(self):
        return self.outputs_q.all()

    @property
    def inputs(self):
        return self.inputs_q.all()

    # children via db_dbpath
    # suggest change name to descendants
    children_q = relationship(
        "DbNode", secondary="db_dbpath",
        primaryjoin="DbNode.id == DbPath.parent_id",
        secondaryjoin="DbNode.id == DbPath.child_id",
        backref=backref("parents_q", passive_deletes=True, lazy='dynamic'),
        lazy='dynamic',
        passive_deletes=True
    )

    @property
    def children(self):
        return self.children_q.all()

    @property
    def parents(self):
        return self.parents_q.all()

    def __init__(self, *args, **kwargs):
        super(DbNode, self).__init__(*args, **kwargs)

        if self.attributes is None:
            self.attributes = dict()

        if self.extras is None:
            self.extras = dict()


    # XXX repetition between django/sqlalchemy here.
    def get_aiida_class(self):
        """
        Return the corresponding aiida instance of class aiida.orm.Node or a
        appropriate subclass.
        """
        from aiida.common.old_pluginloader import from_type_to_pluginclassname
        from aiida.orm.node import Node

        try:
            pluginclassname = from_type_to_pluginclassname(self.type)
        except DbContentError:
            raise DbContentError("The type name of node with pk= {} is "
                                 "not valid: '{}'".format(self.pk, self.type))

        try:
            PluginClass = load_plugin(Node, 'aiida.orm', pluginclassname)
        except MissingPluginError:
            aiidalogger.error("Unable to find plugin for type '{}' (node= {}), "
                              "will use base Node class".format(self.type, self.pk))
            PluginClass = Node

        return PluginClass(dbnode=self)

    def get_simple_name(self, invalid_result=None):
        """
        Return a string with the last part of the type name.

        If the type is empty, use 'Node'.
        If the type is invalid, return the content of the input variable
        ``invalid_result``.

        :param invalid_result: The value to be returned if the node type is
            not recognized.
        """
        thistype = self.type
        # Fix for base class
        if thistype == "":
            thistype = "node.Node."
        if not thistype.endswith("."):
            return invalid_result
        else:
            thistype = thistype[:-1]  # Strip final dot
            return thistype.rpartition('.')[2]

    def set_attr(self, key, value):
        DbNode._set_attr(self.attributes, key, value)
        flag_modified(self, "attributes")
        self.save()

    def set_extra(self, key, value):
        DbNode._set_attr(self.extras, key, value)
        flag_modified(self, "extras")
        self.save()

    def reset_extras(self, new_extras):
        self.extras.clear()
        self.extras.update(new_extras)
        flag_modified(self, "extras")
        self.save()

    def del_attr(self, key):
        DbNode._del_attr(self.attributes, key)
        flag_modified(self, "attributes")
        self.save()

    def del_extra(self, key):
        DbNode._del_attr(self.extras, key)
        flag_modified(self, "extras")
        self.save()

    @staticmethod
    def _set_attr(d, key, value):
        if '.' in key:
            raise ValueError(
                "We don't know how to treat key with dot in it yet")

        d[key] = value

    @staticmethod
    def _del_attr(d, key):
        if '.' in key:
            raise ValueError("We don't know how to treat key with dot in it yet")

        if key not in d:
            raise ValueError("Key {} does not exists".format(key))

        del d[key]

    @property
    def pk(self):
        return self.id

    def __str__(self):
        simplename = self.get_simple_name(invalid_result="Unknown")
        # node pk + type
        if self.label:
            return "{} node [{}]: {}".format(simplename, self.pk, self.label)
        else:
            return "{} node [{}]".format(simplename, self.pk)


    @hybrid_property
    def state(self):
        """
        Return the most recent state from DbCalcState
        """
        if not self.id:
            return None
        all_states = DbCalcState.query.filter(DbCalcState.dbnode_id == self.id).all()
        if all_states:
            #return max((st.time, st.state) for st in all_states)[1]
            return sort_states(((dbcalcstate.state, dbcalcstate.state.value)
                                for dbcalcstate in all_states),
                                use_key=True)[0]
        else:
            return None

    @state.expression
    def state(cls):
        """
        Return the expression to get the 'latest' state from DbCalcState,
        to be used in queries, where 'latest' is defined using the state order
        defined in _sorted_datastates.
        """
        # Sort first the latest states
        whens = {
            v: idx for idx, v
            in enumerate(_sorted_datastates[::-1], start=1)}
        custom_sort_order = case(value=DbCalcState.state,
                                 whens=whens,
                                 else_=100) # else: high value to put it at the bottom

        # Add numerical state to string, to allow to sort them
        states_with_num = select([
            DbCalcState.id.label('id'),
            DbCalcState.dbnode_id.label('dbnode_id'),
            DbCalcState.state.label('state_string'),
            custom_sort_order.label('num_state')
        ]).select_from(DbCalcState).alias()

        # Get the most 'recent' state (using the state ordering, and the min function) for
        # each calc
        calc_state_num = select([
            states_with_num.c.dbnode_id.label('dbnode_id'),
            func.min(states_with_num.c.num_state).label('recent_state')
        ]).group_by(states_with_num.c.dbnode_id).alias()

        # Join the most-recent-state table with the DbCalcState table
        all_states_q = select([
            DbCalcState.dbnode_id.label('dbnode_id'),
            DbCalcState.state.label('state_string'),
            calc_state_num.c.recent_state.label('recent_state'),
            custom_sort_order.label('num_state'),
        ]).select_from(#DbCalcState).alias().join(
            join(DbCalcState, calc_state_num, DbCalcState.dbnode_id == calc_state_num.c.dbnode_id)).alias()

        # Get the association between each calc and only its corresponding most-recent-state row
        subq = select([
            all_states_q.c.dbnode_id.label('dbnode_id'),
            all_states_q.c.state_string.label('state')
        ]).select_from(all_states_q).where(all_states_q.c.num_state == all_states_q.c.recent_state).alias()

        # Final filtering for the actual query
        return select([subq.c.state]).\
            where(
                    subq.c.dbnode_id == cls.id,
                ).\
            label('laststate')


class DbLink(Base):
    __tablename__ = "db_dblink"

    id = Column(Integer, primary_key=True)
    input_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', deferrable=True, initially="DEFERRED")
    )
    output_id = Column(
        Integer,
        ForeignKey(
            'db_dbnode.id',
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED"
        )
    )

    input = relationship("DbNode", primaryjoin="DbLink.input_id == DbNode.id")
    output = relationship("DbNode", primaryjoin="DbLink.output_id == DbNode.id")

    label = Column(String(255), index=True, nullable=False)
    type = Column(String(255))

    # A calculation can have both a 'return' and a 'create' link to
    # a single data output node, which would violate the unique constraint
    # defined below, since the difference in link type is not considered.
    # The distinction between the type of a 'create' and a 'return' link is not
    # implemented at the moment, so the unique constraint is disabled.
    __table_args__ = (
        # I cannot add twice the same link
        # I want unique labels among all inputs of a node
        # UniqueConstraint('output_id', 'label'),
    )

    def __str__(self):
        return "{} ({}) --> {} ({})".format(
            self.input.get_simple_name(invalid_result="Unknown node"),
            self.input.pk,
            self.output.get_simple_name(invalid_result="Unknown node"),
            self.output.pk
        )


class DbPath(Base):
    __tablename__ = "db_dbpath"

    id = Column(Integer, primary_key=True)
    parent_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', deferrable=True, initially="DEFERRED")
    )
    child_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', deferrable=True, initially="DEFERRED")
    )

    parent = relationship(
        "DbNode",
        primaryjoin="DbPath.parent_id == DbNode.id",
        backref="child_paths"
    )
    child = relationship(
        "DbNode",
        primaryjoin="DbPath.child_id == DbNode.id",
        backref="parent_paths"
    )

    depth = Column(Integer)

    entry_edge_id = Column(Integer)
    direct_edge_id = Column(Integer)
    exit_edge_id = Column(Integer)

    def expand(self):
        """
        Method to expand a DbPath (recursive function), i.e., to get a list
        of all dbnodes that are traversed in the given path.

        :return: list of DbNode objects representing the expanded DbPath
        """

        if self.depth == 0:
            return [self.parent_id, self.child_id]
        else:
            path_entry = []
            path_direct = DbPath.query.filter_by(id=self.direct_edge_id).first().expand()
            path_exit = []
            # we prevent DbNode repetitions
            if self.entry_edge_id != self.direct_edge_id:
                path_entry = DbPath.query.filter_by(id=self.entry_edge_id).first().expand()[:-1]
            if self.exit_edge_id != self.direct_edge_id:
                path_exit = DbPath.query.filter_by(id=self.exit_edge_id).first().expand()[1:]

            return path_entry + path_direct + path_exit

