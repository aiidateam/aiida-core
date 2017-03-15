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

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, UniqueConstraint
from sqlalchemy.types import Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB

from aiida.transport import TransportFactory
from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.exceptions import (DbContentError, MissingPluginError,
                                     ConfigurationError)



class DbAuthInfo(Base):
    __tablename__ = "db_dbauthinfo"

    id = Column(Integer, primary_key=True)

    aiidauser_id = Column(Integer, ForeignKey('db_dbuser.id', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    dbcomputer_id = Column(Integer, ForeignKey('db_dbcomputer.id', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))

    aiidauser = relationship('DbUser', backref='authinfos')
    dbcomputer = relationship('DbComputer', backref='authinfos')

    _metadata = Column('metadata', JSONB)
    auth_params = Column(JSONB)

    enabled = Column(Boolean)

    __table_args__ = (
        UniqueConstraint("aiidauser_id", "dbcomputer_id"),
    )

    def __init__(self, *args, **kwargs):
        self._metadata = {}
        self.enabled = True
        super(DbAuthInfo, self).__init__(*args, **kwargs)

    def get_auth_params(self):
        return self.auth_params

    def set_auth_params(self, auth_params):
        self.auth_params = auth_params

    def get_workdir(self):
        try:
            return self._metadata['workdir']
        except KeyError:
            return self.dbcomputer.get_workdir()

    # a method of DbAuthInfo
    def get_transport(self):
        """
        Given a computer and an aiida user (as entries of the DB) return a configured
        transport to connect to the computer.
        """
        from aiida.orm.computer import Computer
        try:
            ThisTransport = TransportFactory(self.dbcomputer.transport_type)
        except MissingPluginError as e:
            raise ConfigurationError('No transport found for {} [type {}], message: {}'.format(
                self.dbcomputer.hostname, self.dbcomputer.transport_type, e.message))

        params = dict(Computer(dbcomputer=self.dbcomputer).get_transport_params().items() +
                      self.get_auth_params().items())
        return ThisTransport(machine=self.dbcomputer.hostname, **params)

    def __str__(self):
        if self.enabled:
            return "Authorization info for {} on {}".format(self.aiidauser.email, self.dbcomputer.name)
        else:
            return "Authorization info for {} on {} [DISABLED]".format(self.aiidauser.email, self.dbcomputer.name)
