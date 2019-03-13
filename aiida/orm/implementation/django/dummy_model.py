# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
The dummy model encodes the model defined by django in backends.djsite
using SQLAlchemy.
This is done to query the database with more performant ORM of SA.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=no-name-in-module, import-error, invalid-name
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, Table, ForeignKey, UniqueConstraint, select)

from sqlalchemy.types import (
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
    Text,
)
from sqlalchemy.orm import (relationship, backref, sessionmaker)

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import UUID

# MISC
from aiida.common import timezone
from aiida.common.utils import get_new_uuid

Base = declarative_base()

# pylint: disable=missing-docstring, too-few-public-methods


class DbLink(Base):
    __tablename__ = "db_dblink"
    id = Column(Integer, primary_key=True)
    input_id = Column(Integer, ForeignKey('db_dbnode.id', deferrable=True, initially="DEFERRED"))
    output_id = Column(Integer, ForeignKey('db_dbnode.id', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    type = Column(String(255))
    input = relationship("DbNode", primaryjoin="DbLink.input_id == DbNode.id")
    output = relationship("DbNode", primaryjoin="DbLink.output_id == DbNode.id")
    label = Column(String(255), index=True, nullable=False)


class DbAttribute(Base):
    __tablename__ = "db_dbattribute"
    id = Column(Integer, primary_key=True)
    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id'))
    key = Column(String(255))
    datatype = Column(String(10))
    tval = Column(String, default='')
    fval = Column(Float, default=None, nullable=True)
    ival = Column(Integer, default=None, nullable=True)
    bval = Column(Boolean, default=None, nullable=True)
    dval = Column(DateTime, default=None, nullable=True)


class DbExtra(Base):
    __tablename__ = "db_dbextra"
    id = Column(Integer, primary_key=True)
    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id'))
    key = Column(String(255))
    datatype = Column(String(10))
    tval = Column(String, default='')
    fval = Column(Float, default=None, nullable=True)
    ival = Column(Integer, default=None, nullable=True)
    bval = Column(Boolean, default=None, nullable=True)
    dval = Column(DateTime, default=None, nullable=True)


class DbComputer(Base):
    __tablename__ = "db_dbcomputer"

    id = Column(Integer, primary_key=True)

    uuid = Column(UUID(as_uuid=True), default=get_new_uuid)
    name = Column(String(255), unique=True, nullable=False)
    hostname = Column(String(255))

    description = Column(Text, nullable=True)
    enabled = Column(Boolean)

    transport_type = Column(String(255))
    scheduler_type = Column(String(255))

    transport_params = Column(String(255))
    _metadata = Column('metadata', String(255), default="{}")


class DbUser(Base):
    __tablename__ = "db_dbuser"

    id = Column(Integer, primary_key=True)
    email = Column(String(254), unique=True, index=True)
    password = Column(String(128))  # Clear text password ?
    first_name = Column(String(254), nullable=True)
    last_name = Column(String(254), nullable=True)
    institution = Column(String(254), nullable=True)

    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)

    last_login = Column(DateTime(timezone=True), default=timezone.now)
    date_joined = Column(DateTime(timezone=True), default=timezone.now)


table_groups_nodes = Table(
    'db_dbgroup_dbnodes', Base.metadata, Column('id', Integer, primary_key=True),
    Column('dbnode_id', Integer, ForeignKey('db_dbnode.id', deferrable=True, initially="DEFERRED")),
    Column('dbgroup_id', Integer, ForeignKey('db_dbgroup.id', deferrable=True, initially="DEFERRED")))


class DbGroup(Base):
    __tablename__ = "db_dbgroup"

    id = Column(Integer, primary_key=True)

    uuid = Column(UUID(as_uuid=True), default=get_new_uuid)
    label = Column(String(255), index=True)

    type_string = Column(String(255), default="", index=True)

    time = Column(DateTime(timezone=True), default=timezone.now)
    description = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially="DEFERRED"))
    user = relationship('DbUser', backref=backref('dbgroups', cascade='merge'))

    dbnodes = relationship('DbNode', secondary=table_groups_nodes, backref="dbgroups", lazy='dynamic')

    __table_args__ = (UniqueConstraint('label', 'type_string'),)

    def __str__(self):
        return '<DbGroup [type: {}] "{}">'.format(self.type_string, self.label)


class DbNode(Base):
    __tablename__ = "db_dbnode"
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid)
    node_type = Column(String(255), index=True)
    process_type = Column(String(255), index=True)
    label = Column(String(255), index=True, nullable=True)
    description = Column(Text(), nullable=True)
    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now)
    dbcomputer_id = Column(
        Integer, ForeignKey('db_dbcomputer.id', deferrable=True, initially="DEFERRED"), nullable=True)
    dbcomputer = relationship('DbComputer', backref=backref('dbnodes', passive_deletes=True))
    user_id = Column(Integer, ForeignKey('db_dbuser.id', deferrable=True, initially="DEFERRED"), nullable=False)
    user = relationship('DbUser', backref='dbnodes')

    public = Column(Boolean, default=False)

    nodeversion = Column(Integer, default=1)

    attributes = relationship('DbAttribute', uselist=True, backref='dbnode')
    extras = relationship('DbExtra', uselist=True, backref='dbnode')

    outputs = relationship(
        "DbNode",
        secondary="db_dblink",
        primaryjoin="DbNode.id == DbLink.input_id",
        secondaryjoin="DbNode.id == DbLink.output_id",
        backref=backref("inputs", passive_deletes=True),
        passive_deletes=True)

    @hybrid_property
    def user_email(self):
        """
        Returns: the email of the user
        """
        return self.user.email

    @user_email.expression
    def user_email(self):
        """
        Returns: the email of the user at a class level (i.e. in the database)
        """
        return select([DbUser.email]).where(DbUser.id == self.user_id).label('user_email')

    # Computer name
    @hybrid_property
    def computer_name(self):
        """
        Returns: the of the computer
        """
        return self.dbcomputer.name

    @computer_name.expression
    def computer_name(self):
        """
        Returns: the name of the computer at a class level (i.e. in the database)
        """
        return select([DbComputer.name]).where(DbComputer.id == self.dbcomputer_id).label('computer_name')


class DbAuthInfo(Base):
    __tablename__ = "db_dbauthinfo"

    id = Column(Integer, primary_key=True)

    aiidauser_id = Column(Integer, ForeignKey(
        'db_dbuser.id', ondelete='CASCADE', deferrable=True, initially="DEFERRED"))
    aiidauser = relationship('DbUser', backref=backref('dbauthinfo', cascade='merge'))
    dbcomputer_id = Column(Integer,
                           ForeignKey('db_dbcomputer.id', ondelete='CASCADE', deferrable=True, initially="DEFERRED"))
    dbcomputer = relationship('DbComputer', backref=backref('dbauthinfo', passive_deletes=True))
    _metadata = Column('metadata', String(255), default="{}")
    auth_params = Column('auth_params', String(255), default="{}")

    enabled = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("aiidauser_id", "dbcomputer_id"),)


class DbLog(Base):
    __tablename__ = "db_dblog"

    id = Column(Integer, primary_key=True)

    uuid = Column(UUID(as_uuid=True), default=get_new_uuid)

    time = Column(DateTime(timezone=True), default=timezone.now)
    loggername = Column(String(255), index=True)
    levelname = Column(String(255), index=True)

    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id', deferrable=True, initially="DEFERRED"), nullable=True)
    dbnode = relationship('DbNode', backref=backref('dblogs', passive_deletes=True))

    message = Column(Text(), nullable=True)
    _metadata = Column('metadata', String(255), default="{}")


class DbComment(Base):
    __tablename__ = "db_dbcomment"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid)
    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))

    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now, onupdate=timezone.now)

    user_id = Column(Integer, ForeignKey('db_dbuser.id', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    content = Column(Text, nullable=True)

    dbnode = relationship('DbNode', backref='dbcomments')
    user = relationship("DbUser")


def get_aldjemy_session():
    """
    Use aldjemy to make a session

    .. note:
        Use only in this case. In normal production mode
        it is safer make session explictly because it is more robust
    """
    from aldjemy.core import get_engine
    engine = get_engine()
    _Session = sessionmaker(bind=engine)
    return _Session()


session = get_aldjemy_session()
