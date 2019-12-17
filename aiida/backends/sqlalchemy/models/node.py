# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module
"""Module to manage nodes for the SQLA backend."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, DateTime, Text
# Specific to PGSQL. If needed to be agnostic
# http://docs.sqlalchemy.org/en/rel_0_9/core/custom_types.html?highlight=guid#backend-agnostic-guid-type
# Or maybe rely on sqlalchemy-utils UUID type
from sqlalchemy.dialects.postgresql import UUID, JSONB

from aiida.common import timezone
from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.utils import get_new_uuid


class DbNode(Base):
    """Class to store nodes using SQLA backend."""

    __tablename__ = 'db_dbnode'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, unique=True)
    node_type = Column(String(255), index=True)
    process_type = Column(String(255), index=True)
    label = Column(
        String(255), index=True, nullable=True, default=''
    )  # Does it make sense to be nullable and have a default?
    description = Column(Text(), nullable=True, default='')
    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now, onupdate=timezone.now)
    attributes = Column(JSONB)
    extras = Column(JSONB)

    dbcomputer_id = Column(
        Integer,
        ForeignKey('db_dbcomputer.id', deferrable=True, initially='DEFERRED', ondelete='RESTRICT'),
        nullable=True
    )

    # This should have the same ondelete behaviour as db_computer_id, right?
    user_id = Column(
        Integer, ForeignKey('db_dbuser.id', deferrable=True, initially='DEFERRED', ondelete='restrict'), nullable=False
    )

    # TODO SP: The 'passive_deletes=all' argument here means that SQLAlchemy
    # won't take care of automatic deleting in the DbLink table. This still
    # isn't exactly the same behaviour than with Django. The solution to
    # this is probably a ON DELETE inside the DB. On removing node with id=x,
    # we would remove all link with x as an output.

    dbcomputer = relationship('DbComputer', backref=backref('dbnodes', passive_deletes='all', cascade='merge'))

    # User
    user = relationship('DbUser', backref=backref(
        'dbnodes',
        passive_deletes='all',
        cascade='merge',
    ))

    # outputs via db_dblink table
    outputs_q = relationship(
        'DbNode',
        secondary='db_dblink',
        primaryjoin='DbNode.id == DbLink.input_id',
        secondaryjoin='DbNode.id == DbLink.output_id',
        backref=backref('inputs_q', passive_deletes=True, lazy='dynamic'),
        lazy='dynamic',
        passive_deletes=True
    )

    def __init__(self, *args, **kwargs):
        """Add three additional attributes to the base class: mtime, attributes and extras."""
        super().__init__(*args, **kwargs)
        # The behavior of an unstored Node instance should be that all its attributes should be initialized in
        # accordance with the defaults specified on the colums, i.e. if a default is specified for the `uuid` column,
        # then an unstored `DbNode` instance should have a default value for the `uuid` attribute. The exception here
        # is the `mtime`, that we do not want to be set upon instantiation, but only upon storing. However, in
        # SqlAlchemy a default *has* to be defined if one wants to get that value upon storing. But since defining a
        # default on the column in combination with the hack in `aiida.backend.SqlAlchemy.models.__init__` to force all
        # defaults to be populated upon instantiation, we have to unset the `mtime` attribute here manually.
        #
        # The only time that we allow mtime not to be null is when we explicitly pass mtime as a kwarg. This covers
        # the case that a node is constructed based on some very predefined data like when we create nodes at the
        # AiiDA import functions.
        if 'mtime' not in kwargs:
            self.mtime = None

        if self.attributes is None:
            self.attributes = dict()

        if self.extras is None:
            self.extras = dict()

    @property
    def outputs(self):
        return self.outputs_q.all()

    @property
    def inputs(self):
        return self.inputs_q.all()

    def get_simple_name(self, invalid_result=None):
        """
        Return a string with the last part of the type name.

        If the type is empty, use 'Node'.
        If the type is invalid, return the content of the input variable
        ``invalid_result``.

        :param invalid_result: The value to be returned if the node type is
            not recognized.
        """
        thistype = self.node_type
        # Fix for base class
        if thistype == '':
            thistype = 'node.Node.'
        if not thistype.endswith('.'):
            return invalid_result
        thistype = thistype[:-1]  # Strip final dot
        return thistype.rpartition('.')[2]

    @property
    def pk(self):
        return self.id

    def __str__(self):
        """Get string object out of DbNode object."""
        simplename = self.get_simple_name(invalid_result='Unknown')
        # node pk + type
        if self.label:
            return '{} node [{}]: {}'.format(simplename, self.pk, self.label)
        return '{} node [{}]'.format(simplename, self.pk)


class DbLink(Base):
    """Class to store links between nodes using SQLA backend."""

    __tablename__ = 'db_dblink'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    input_id = Column(Integer, ForeignKey('db_dbnode.id', deferrable=True, initially='DEFERRED'), index=True)
    output_id = Column(
        Integer, ForeignKey('db_dbnode.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'), index=True
    )

    input = relationship('DbNode', primaryjoin='DbLink.input_id == DbNode.id')
    output = relationship('DbNode', primaryjoin='DbLink.output_id == DbNode.id')

    label = Column(String(255), index=True, nullable=False)
    type = Column(String(255), index=True)

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
        return '{} ({}) --> {} ({})'.format(
            self.input.get_simple_name(invalid_result='Unknown node'), self.input.pk,
            self.output.get_simple_name(invalid_result='Unknown node'), self.output.pk
        )
