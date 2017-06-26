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

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import (
    Column, Table, ForeignKey, UniqueConstraint,create_engine,
    select, func, join, and_, or_, not_, except_, case, exists,
    text
)

from sqlalchemy.types import (
    Integer, String, DateTime, Float, Boolean, Text,
)
from sqlalchemy.orm import (
    relationship,
    backref,
    sessionmaker,
    foreign, mapper, aliased
)

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import Cast
from sqlalchemy.dialects.postgresql import UUID, JSONB, INTEGER, array
# TO COMPILE MY OWN FUNCTIONALITIES:
from sqlalchemy.sql.expression import FunctionElement, cast
from sqlalchemy.sql.base import ImmutableColumnCollection
from sqlalchemy.ext.compiler import compiles

# Aiida Django classes:
#from aiida.orm.implementation.django.node import Node as DjangoAiidaNode

#from aiida.common.pluginloader import load_plugin


# SETTINGS:
from aiida.common.setup import get_profile_config
from aiida.backends import settings

#EXCEPTIONS
from aiida.common.exceptions import DbContentError, MissingPluginError

# MISC
from aiida.backends.sqlalchemy.models.utils import uuid_func
from aiida.utils import timezone
from aiida.common.datastructures import (calc_states, _sorted_datastates,
                                         sort_states)

Base = declarative_base()

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
    type=Column(String(255))
    input = relationship("DbNode", primaryjoin="DbLink.input_id == DbNode.id")
    output = relationship("DbNode", primaryjoin="DbLink.output_id == DbNode.id")
    label = Column(String(255), index=True, nullable=False)


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

class DbCalcState(Base):
    __tablename__ = "db_dbcalcstate"
    id = Column(Integer, primary_key=True)
    dbnode = relationship(
            'DbNode',
            backref=backref('dbstates', passive_deletes=True)
        )
    state = Column(String(255))
    time = Column(DateTime(timezone=True), default=timezone.now)
    dbnode_id = Column(
            Integer,
            ForeignKey(
                'db_dbnode.id', ondelete="CASCADE",
                deferrable=True, initially="DEFERRED"
            )
        )
    __table_args__ = (
        UniqueConstraint('dbnode_id', 'state'),
    )

class DbAttribute(Base):
    __tablename__ = "db_dbattribute"
    id  = Column(Integer, primary_key = True)
    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id'))
    key = Column(String(255))
    datatype = Column(String(10))
    tval = Column(String, default='')
    fval = Column(Float, default=None, nullable=True)
    ival = Column(Integer, default=None, nullable=True)
    bval = Column(Boolean, default=None, nullable=True)
    dval = Column(DateTime, default=None, nullable = True)



class DbExtra(Base):
    __tablename__ = "db_dbextra"
    id  = Column(Integer, primary_key = True)
    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id'))
    key = Column(String(255))
    datatype = Column(String(10))
    tval = Column(String, default='')
    fval = Column(Float, default=None, nullable=True)
    ival = Column(Integer, default=None, nullable=True)
    bval = Column(Boolean, default=None, nullable=True)
    dval = Column(DateTime, default=None, nullable = True)


class DbComputer(Base):
    __tablename__ = "db_dbcomputer"

    id = Column(Integer, primary_key=True)

    uuid = Column(UUID(as_uuid=True), default=uuid_func)
    name = Column(String(255), unique=True, nullable=False)
    hostname = Column(String(255))

    description = Column(Text, nullable=True)
    enabled = Column(Boolean)

    transport_type = Column(String(255))
    scheduler_type = Column(String(255))

    transport_params = Column(String(255))
    _metadata = Column('metadata', String(255), default="{}")

    def get_aiida_class(self):
        from aiida.backends.djsite.db.models import DbComputer as DjangoSchemaDbComputer
        djcomputer = DjangoSchemaDbComputer(
            id=self.id, uuid=self.uuid, name=self.name,
            hostname=self.hostname, description=self.description,
            enabled=self.enabled, transport_type=self.transport_type,
            scheduler_type=self.scheduler_type, transport_params=self.transport_params,
            metadata=self._metadata
        )
        return djcomputer.get_aiida_class()

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

    def get_aiida_class(self):
        from aiida.backends.djsite.db.models import DbUser as DjangoSchemaDbUser
        djuser = DjangoSchemaDbUser(
            id=self.id,email=self.email, password=self.password,
            first_name=self.first_name, last_name=self.last_name,
            institution=self.institution, is_staff=self.is_staff,
            is_active=self.is_active, last_login=self.last_login,
            date_joined=self.date_joined
        )
        return djuser.get_aiida_class()


table_groups_nodes = Table(
    'db_dbgroup_dbnodes',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column(
            'dbnode_id', Integer,
            ForeignKey('db_dbnode.id', deferrable=True, initially="DEFERRED")
        ),
    Column(
            'dbgroup_id', Integer,
            ForeignKey('db_dbgroup.id', deferrable=True, initially="DEFERRED")
        )
)

class DbGroup(Base):
    __tablename__ = "db_dbgroup"

    id = Column(Integer, primary_key=True)

    uuid = Column(UUID(as_uuid=True), default=uuid_func)
    name = Column(String(255), index=True)

    type = Column(String(255), default="", index=True)

    time = Column(DateTime(timezone=True), default=timezone.now)
    description = Column(Text, nullable=True)

    user_id = Column(
            Integer,
            ForeignKey(
                'db_dbuser.id', ondelete='CASCADE',
                deferrable=True, initially="DEFERRED")
            )
    user = relationship('DbUser', backref=backref('dbgroups', cascade='merge'))

    dbnodes = relationship('DbNode', secondary=table_groups_nodes,
                           backref="dbgroups", lazy='dynamic')

    __table_args__ = (
        UniqueConstraint('name', 'type'),
    )

    def __str__(self):
        if self.type:
            return '<DbGroup [type: {}] "{}">'.format(self.type, self.name)
        else:
            return '<DbGroup [user-defined] "{}">'.format(self.name)
    def get_aiida_class(self):
        from aiida.orm.implementation.django.group import Group as DjangoAiidaGroup
        from aiida.backends.djsite.db.models import DbGroup as DjangoSchemaDbGroup
        dbgroup = DjangoSchemaDbGroup(
            id = self.id,
            type = self.type,
            uuid = self.uuid,
            name = self.name,
            time = self.time,
            description  = self.description,
            user_id = self.user_id,
        )

        return DjangoAiidaGroup(dbgroup=dbgroup)



class DbNode(Base):
    __tablename__ = "db_dbnode"
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid_func)
    type = Column(String(255), index=True)
    label = Column(String(255), index=True, nullable=True)
    description = Column(Text(), nullable=True)
    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now)
    dbcomputer_id = Column(
        Integer,
        ForeignKey('db_dbcomputer.id', deferrable=True, initially="DEFERRED"),
        nullable=True
    )
    dbcomputer = relationship(
        'DbComputer',
        backref=backref('dbnodes', passive_deletes=True)
    )
    user_id = Column(
        Integer,
        ForeignKey('db_dbuser.id', deferrable=True, initially="DEFERRED"),
        nullable=False
    )
    user = relationship('DbUser', backref='dbnodes')

    public = Column(Boolean, default=False)

    nodeversion = Column(Integer, default=1)

    attributes = relationship('DbAttribute', uselist=True, backref='dbnode')
    extras = relationship('DbExtra', uselist=True, backref='dbnode')



    outputs = relationship(
        "DbNode",
        secondary       =   "db_dblink",
        primaryjoin     =   "DbNode.id == DbLink.input_id",
        secondaryjoin   =   "DbNode.id == DbLink.output_id",
        backref         =   backref("inputs", passive_deletes=True),
        passive_deletes =   True
    )

    children = relationship(
        "DbNode",
        secondary       =   "db_dbpath",
        primaryjoin     =   "DbNode.id == DbPath.parent_id",
        secondaryjoin   =   "DbNode.id == DbPath.child_id",
        backref         =   "parents"
    )
    def get_aiida_class(self):
        """
        Return the corresponding instance of
        :func:`~aiida.orm.implementation.django.node.Node`
        or a subclass return by the plugin loader.

        .. todo::
            The behavior is quite pathetic, creating a django DbNode instance
            to instantiate the aiida instance.
            These means that every time you load Aiida instances with
            the QueryBuilder when using Django as a backend, three instances
            are instantiated for every Aiida instance you load!
            Could be fixed by allowing DbNode from the dummy nodel to be passed
            to AiidaNode's __init__.

        :returns: An instance of the plugin class
        """
        # I need to import the DbNode in the Django model,
        # and instantiate an object that has the same attributes as self.
        from aiida.backends.djsite.db.models import DbNode as DjangoSchemaDbNode
        dbnode = DjangoSchemaDbNode(
                id=self.id, type=self.type, uuid=self.uuid, ctime=self.ctime,
                mtime=self.mtime, label=self.label,
                description=self.description, dbcomputer_id=self.dbcomputer_id,
                user_id=self.user_id, public=self.public,
                nodeversion=self.nodeversion
        )
        return dbnode.get_aiida_class()


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




profile = get_profile_config(settings.AIIDADB_PROFILE)


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


