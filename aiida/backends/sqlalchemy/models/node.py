# -*- coding: utf-8 -*-

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref, Query
from sqlalchemy.schema import Column, UniqueConstraint
from sqlalchemy.types import Integer, String, Boolean, DateTime, Text
# Specific to PGSQL. If needed to be agnostic
# http://docs.sqlalchemy.org/en/rel_0_9/core/custom_types.html?highlight=guid#backend-agnostic-guid-type
# Or maybe rely on sqlalchemy-utils UUID type
from sqlalchemy.dialects.postgresql import UUID, JSONB

from aiida.utils import timezone
from aiida.backends.sqlalchemy.models.base import Base, _QueryProperty, _AiidaQuery
from aiida.backends.sqlalchemy.models.utils import uuid_func

from aiida.common import aiidalogger
from aiida.common.pluginloader import load_plugin
from aiida.common.exceptions import DbContentError, MissingPluginError


class DbLink(Base):
    __tablename__ = "db_dblink"

    id = Column(Integer, primary_key=True)
    input_id = Column(Integer, ForeignKey('db_dbnode.id'))
    output_id = Column(Integer, ForeignKey('db_dbnode.id'))

    label = Column(String(255), index=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('input_id', 'output_id'),
        UniqueConstraint('output_id', 'label'),
    )

    def __str__(self):
        return "{} ({}) --> {} ({})".format(
            self.input.get_simple_name(invalid_result="Unknown node"),
            self.input.pk,
            self.output.get_simple_name(invalid_result="Unknown node"),
            self.output.pk, )


class DbPath(Base):
    __tablename__ = "db_dbpath"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('db_dbnode.id'))
    child_id = Column(Integer, ForeignKey('db_dbnode.id'))

    depth = Column(Integer)

    entry_edge_id = Column(Integer, ForeignKey('db_dbnode.id'))
    direct_edge_id = Column(Integer, ForeignKey('db_dbnode.id'))
    exit_edge_id = Column(Integer, ForeignKey('db_dbnode.id'))

    __table_args__ = (
        UniqueConstraint('parent_id', 'child_id'),
    )


class DbNode(Base):
    __tablename__ = "db_dbnode"

    aiida_query = _QueryProperty(_AiidaQuery)

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID, default=uuid_func)

    type = Column(String(255), index=True)
    label = Column(String(255), index=True, nullable=True)
    description = Column(Text(), nullable=True)

    # TODO SP: compare to the django's implementation, you can either delete an
    # output or an output, with no restriction. This might need to be explored.
    outputs = relationship("DbNode", secondary="db_dblink",
                           primaryjoin="DbNode.id == DbLink.input_id",
                           secondaryjoin="DbNode.id == DbLink.output_id",
                           backref="inputs", lazy="dynamic")

    child_paths = relationship("DbNode", secondary="db_dbpath",
                               primaryjoin="DbNode.id == DbPath.parent_id",
                               secondaryjoin="DbNode.id == DbPath.child_id",
                               backref="parent_paths", lazy="dynamic")

    # TODO SP: prevent modification
    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now)

    # TODO SP: on delete here should not be needed. The default behaviour from
    # any sane database is to prevent removal of an row if other row are
    # referencing it.
    dbcomputer_id = Column(Integer, ForeignKey('db_dbcomputer.id'),
                         nullable=True)
    dbcomputer = relationship('DbComputer', backref=backref('dbnodes'))

    user_id = Column(Integer, ForeignKey('db_dbuser.id'), nullable=False)
    user = relationship('DbUser', backref='dbnodes')

    nodeversion = Column(Integer, default=False)

    attributes = Column(JSONB, default={})

    # TODO SP: repetition between django/sqlalchemy here.
    def get_aiida_class(self):
        """
        Return the corresponding aiida instance of class aiida.orm.Node or a
        appropriate subclass.
        """
        from aiida.orm import from_type_to_pluginclassname
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

    @property
    def extras(self):
        """
        Return all extras of the given node as a single dictionary.
        """
        # TODO SP: extra attributes

    def __str__(self):
        simplename = self.get_simple_name(invalid_result="Unknown")
        # node pk + type
        if self.label:
            return "{} node [{}]: {}".format(simplename, self.pk, self.label)
        else:
            return "{} node [{}]".format(simplename, self.pk)
