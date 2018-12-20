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
from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Boolean, DateTime, Text
# Specific to PGSQL. If needed to be agnostic
# http://docs.sqlalchemy.org/en/rel_0_9/core/custom_types.html?highlight=guid#backend-agnostic-guid-type
# Or maybe rely on sqlalchemy-utils UUID type
from sqlalchemy.dialects.postgresql import UUID, JSONB

from aiida.common import timezone
from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.models.utils import uuid_func
from aiida.backends.sqlalchemy.utils import flag_modified
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.backends.sqlalchemy.models.computer import DbComputer


class DbNode(Base):
    __tablename__ = "db_dbnode"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid_func, unique=True)
    type = Column(String(255), index=True)
    process_type = Column(String(255), index=True)
    label = Column(String(255), index=True, nullable=True,
                   default="")  # Does it make sense to be nullable and have a default?
    description = Column(Text(), nullable=True, default="")
    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now, onupdate=timezone.now)
    nodeversion = Column(Integer, default=1)
    public = Column(Boolean, default=False)
    attributes = Column(JSONB)
    extras = Column(JSONB)

    dbcomputer_id = Column(
        Integer,
        ForeignKey('db_dbcomputer.id', deferrable=True, initially="DEFERRED", ondelete="RESTRICT"),
        nullable=True
    )

    # This should have the same ondelete behaviour as db_computer_id, right?
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
        backref=backref('dbnodes', passive_deletes='all', cascade='merge', )
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

    def __init__(self, *args, **kwargs):
        super(DbNode, self).__init__(*args, **kwargs)

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
            raise ValueError("We don't know how to treat key with dot in it yet")

        d[key] = value

    @staticmethod
    def _del_attr(d, key):
        if '.' in key:
            raise ValueError("We don't know how to treat key with dot in it yet")

        if key not in d:
            raise AttributeError("Key {} does not exists".format(key))

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

    # User email
    @hybrid_property
    def user_email(self):
        """
        Returns: the email of the user
        """
        return self.user.email

    @user_email.expression
    def user_email(cls):
        """
        Returns: the email of the user at a class level (i.e. in the database)
        """
        return select([DbUser.email]).where(DbUser.id == cls.user_id).label(
            'user_email')

    # Computer name
    @hybrid_property
    def computer_name(self):
        """
        Returns: the of the computer
        """
        return self.dbcomputer.name

    @computer_name.expression
    def computer_name(cls):
        """
        Returns: the name of the computer at a class level (i.e. in the database)
        """
        return select([DbComputer.name]).where(DbComputer.id ==
                                               cls.dbcomputer_id).label(
            'computer_name')


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
