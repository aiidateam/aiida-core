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

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, UniqueConstraint
from sqlalchemy.types import Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class DbAuthInfo(Base):
    __tablename__ = "db_dbauthinfo"

    id = Column(Integer, primary_key=True)

    aiidauser_id = Column(Integer,
                          ForeignKey('db_dbuser.id', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    dbcomputer_id = Column(Integer,
                           ForeignKey('db_dbcomputer.id', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))

    aiidauser = relationship('DbUser', backref='authinfos')
    dbcomputer = relationship('DbComputer', backref='authinfos')

    _metadata = Column('metadata', JSONB)
    auth_params = Column(JSONB)

    enabled = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("aiidauser_id", "dbcomputer_id"),
    )

    def __init__(self, *args, **kwargs):
        self._metadata = dict()
        self.auth_params = dict()
        super(DbAuthInfo, self).__init__(*args, **kwargs)

    def __str__(self):
        if self.enabled:
            return "DB authorization info for {} on {}".format(self.aiidauser.email, self.dbcomputer.name)
        else:
            return "DB authorization info for {} on {} [DISABLED]".format(self.aiidauser.email, self.dbcomputer.name)
