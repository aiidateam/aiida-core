# -*- coding: utf-8 -*-

import json

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Boolean, Text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from sqlalchemy.dialects.postgresql import UUID, JSONB

from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.models.utils import uuid_func

from aiida.common.exceptions import NotExistent, DbContentError, ConfigurationError


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1"


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

    transport_params = Column(JSONB)
    _metadata = Column('metadata', JSONB)

    #We do not need this relationship from parent to child because we already have one from child to parent which uses backref flag and you add it to either class. See http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html One-to-many relations. Additionally, I decided to put it in the child because I need to use passive_deletes='all' which does not work with maby-to-one (node to computer) relationship which would be the case (instead we have the opposite one to many (computer to node))
    # dbnodes_q = relationship(
    #         'DbNode',
    #         backref=backref('dbnodes'),
    #         lazy='dynamic',
    #     )

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self._metadata = {}
        self.transport_params = {}
        # TODO SP: it's supposed to be nullable, but there is a NOT NULL
        # constraint inside the DB.
        self.description= ""

        super(DbComputer, self).__init__(*args, **kwargs)

    @classmethod
    def get_dbcomputer(cls, computer):
        """
        Return a DbComputer from its name (or from another Computer or DbComputer instance)
        """

        from aiida.orm.computer import Computer
        if isinstance(computer, basestring):
            try:
                dbcomputer = cls.session.query(cls).filter(cls.name==computer).one()
            except NoResultFound:
                raise NotExistent("No computer found in the table of computers with "
                                  "the given name '{}'".format(computer))
            except MultipleResultsFound:
                raise DbContentError("There is more than one computer with name '{}', "
                                     "pass a Computer instance".format(computer))
        elif isinstance(computer, int):
            try:
                dbcomputer = cls.session.query(cls).filter(cls.id==computer).one()
            except NoResultFound:
                raise NotExistent("No computer found in the table of computers with "
                                  "the given id '{}'".format(computer))
        elif isinstance(computer, DbComputer):
            if computer.id is None:
                raise ValueError("The computer instance you are passing has not been stored yet")
            dbcomputer = computer
        elif isinstance(computer, Computer):
            if computer.dbcomputer.id is None:
                raise ValueError("The computer instance you are passing has not been stored yet")
            dbcomputer = computer.dbcomputer
        else:
            raise TypeError("Pass either a computer name, a DbComputer SQLAlchemy instance, a Computer id or a Computer object")
        return dbcomputer

    def get_aiida_class(self):
        from aiida.orm.computer import Computer
        return Computer(dbcomputer=self)

    def get_workdir(self):
        try:
            return self._metadata['workdir']
        except KeyError:
            raise ConfigurationError('No workdir found for DbComputer {} '.format(
                self.name))


    def __str__(self):
        if self.enabled:
            return "{} ({})".format(self.name, self.hostname)
        else:
            return "{} ({}) [DISABLED]".format(self.name, self.hostname)
