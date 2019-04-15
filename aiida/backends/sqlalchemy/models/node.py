# -*- coding: utf-8 -*-

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref, Query
from sqlalchemy.orm.attributes import flag_modified
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


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

class DbLink(Base):
    __tablename__ = "db_dblink"

    id = Column(Integer, primary_key=True)
    input_id = Column(Integer, ForeignKey('db_dbnode.id', deferrable=True, initially="DEFERRED"))
    output_id = Column(Integer, ForeignKey('db_dbnode.id', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))

    input = relationship("DbNode", primaryjoin="DbLink.input_id == DbNode.id")
    output = relationship("DbNode", primaryjoin="DbLink.output_id == DbNode.id")


    label = Column(String(255), index=True, nullable=False)
    type = Column(String(255))

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
    parent_id = Column(Integer, ForeignKey('db_dbnode.id', deferrable=True, initially="DEFERRED"))
    child_id = Column(Integer, ForeignKey('db_dbnode.id', deferrable=True, initially="DEFERRED"))

    parent = relationship("DbNode", primaryjoin="DbPath.parent_id == DbNode.id",
                          backref="child_paths")
    child = relationship("DbNode", primaryjoin="DbPath.child_id == DbNode.id",
                         backref="parent_paths")

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


class DbNode(Base):
    __tablename__ = "db_dbnode"

    aiida_query = _QueryProperty(_AiidaQuery)

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid_func)

    type = Column(String(255), index=True)
    label = Column(String(255), index=True, nullable=True)
    description = Column(Text(), nullable=True)

    # TODO SP: The 'passive_deletes=all' argument here means that SQLAlchemy
    # won't take care of automatic deleting in the DbLink table. This still
    # isn't exactly the same behaviour than with Django. The solution to
    # this is probably a ON DELETE inside the DB. On removing node with id=x,
    # we would remove all link with x as an output.
    outputs = relationship("DbNode", secondary="db_dblink",
                           primaryjoin="DbNode.id == DbLink.input_id",
                           secondaryjoin="DbNode.id == DbLink.output_id",
                           backref=backref("inputs", passive_deletes=True),
                           passive_deletes=True)

    children = relationship("DbNode", secondary="db_dbpath",
                               primaryjoin="DbNode.id == DbPath.parent_id",
                               secondaryjoin="DbNode.id == DbPath.child_id",
                               backref="parents")

    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now)

    dbcomputer_id = Column(Integer, ForeignKey('db_dbcomputer.id', deferrable=True, initially="DEFERRED"),
                         nullable=True)
    dbcomputer = relationship('DbComputer', backref=backref('dbnodes', passive_deletes=True))

    user_id = Column(Integer, ForeignKey('db_dbuser.id', deferrable=True, initially="DEFERRED"), nullable=False)
    user = relationship('DbUser', backref='dbnodes')

    public = Column(Boolean, default=False)

    nodeversion = Column(Integer, default=1)

    attributes = Column(JSONB, default={})
    extras = Column(JSONB, default={})

    def __init__(self, *args, **kwargs):
        self.description = ""
        self.label = ""
        self.public = False
        self.nodeversion = 1
        self.attributes = {}
        self.extras = {}
        super(DbNode, self).__init__(*args, **kwargs)

    # XXX repetition between django/sqlalchemy here.
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

    def set_attr(self, key, value):
        DbNode._set_attr(self.attributes, key, value)
        flag_modified(self, "attributes")

    def set_extra(self, key, value):
        DbNode._set_attr(self.extras, key, value)
        flag_modified(self, "extras")

    def del_attr(self, key):
        DbNode._del_attr(self.attributes, key)
        flag_modified(self, "attributes")

    def del_extra(self, key):
        DbNode._del_attr(self.extras, key)
        flag_modified(self, "extras")

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
            raise ValueError("Key {} does not exists".format(key))

        del d[key]

    def __str__(self):
        simplename = self.get_simple_name(invalid_result="Unknown")
        # node pk + type
        if self.label:
            return "{} node [{}]: {}".format(simplename, self.pk, self.label)
        else:
            return "{} node [{}]".format(simplename, self.pk)
