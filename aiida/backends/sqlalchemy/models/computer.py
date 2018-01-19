# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import json

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Boolean, Text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from sqlalchemy.dialects.postgresql import UUID, JSONB

from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.models.utils import uuid_func

from aiida.common.exceptions import NotExistent, DbContentError, ConfigurationError




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

    def get_shebang(self):
        try:
            return self._metadata['shebang']
        except KeyError:
            raise ConfigurationError('No shebang found for DbComputer {} '.format(
                self.name))

    @property
    def pk(self):
        return self.id

    def __str__(self):
        if self.enabled:
            return "{} ({})".format(self.name, self.hostname)
        else:
            return "{} ({}) [DISABLED]".format(self.name, self.hostname)
