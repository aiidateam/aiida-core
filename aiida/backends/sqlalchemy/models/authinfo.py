# -*- coding: utf-8 -*-

import json

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, UniqueConstraint
from sqlalchemy.types import Integer, Boolean, Text

from aiida.transport import TransportFactory
from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.exceptions import (DbContentError, MissingPluginError,
                                     ConfigurationError)


class DbAuthInfo(Base):
    __tablename__ = "db_dbauthinfo"

    id = Column(Integer, primary_key=True)

    aiidauser_id = Column(Integer, ForeignKey('db_dbuser.id', ondelete="CASCADE"))
    dbcomputer_id = Column(Integer, ForeignKey('db_dbcomputer.id', ondelete="CASCADE"))

    aiidauser = relationship('DbUser')
    dbcomputer = relationship('DbComputer')

    # TODO SP: JSON
    _metadata = Column('metadata', Text, default="{}")

    enabled = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("aiidauser_id", "dbcomputer_id"),
    )

    def get_auth_params(self):
        try:
            return json.loads(self.auth_params)
        except ValueError:
            raise DbContentError(
                "Error while reading auth_params for authinfo, aiidauser={}, computer={}".format(
                    self.aiidauser.email, self.dbcomputer.hostname))

    def set_auth_params(self, auth_params):
        # Raises ValueError if data is not JSON-serializable
        self.auth_params = json.dumps(auth_params)

    def get_workdir(self):
        try:
            metadata = json.loads(self._metadata)
        except ValueError:
            raise DbContentError(
                "Error while reading metadata for authinfo, aiidauser={}, computer={}".format(
                    self.aiidauser.email, self.dbcomputer.hostname))

        try:
            return metadata['workdir']
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
