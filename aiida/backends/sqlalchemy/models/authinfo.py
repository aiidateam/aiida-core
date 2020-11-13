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
"""Module to manage authentification information for the SQLA backend."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, UniqueConstraint
from sqlalchemy.types import Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class DbAuthInfo(Base):
    """Class that keeps the authernification data."""
    __tablename__ = 'db_dbauthinfo'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name

    aiidauser_id = Column(
        Integer, ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED')
    )
    dbcomputer_id = Column(
        Integer, ForeignKey('db_dbcomputer.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED')
    )

    aiidauser = relationship('DbUser', backref='authinfos')
    dbcomputer = relationship('DbComputer', backref='authinfos')

    _metadata = Column('metadata', JSONB)
    auth_params = Column(JSONB)

    enabled = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint('aiidauser_id', 'dbcomputer_id'),)

    def __init__(self, *args, **kwargs):
        self._metadata = dict()
        self.auth_params = dict()
        super().__init__(*args, **kwargs)

    def __str__(self):
        if self.enabled:
            return f'DB authorization info for {self.aiidauser.email} on {self.dbcomputer.name}'
        return f'DB authorization info for {self.aiidauser.email} on {self.dbcomputer.name} [DISABLED]'
