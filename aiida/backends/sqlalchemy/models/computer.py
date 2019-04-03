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

from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Text

from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.utils import get_new_uuid


class DbComputer(Base):

    __tablename__ = 'db_dbcomputer'

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, unique=True)
    name = Column(String(255), unique=True, nullable=False)
    hostname = Column(String(255))
    description = Column(Text, nullable=True)
    transport_type = Column(String(255))
    scheduler_type = Column(String(255))
    transport_params = Column(JSONB)
    _metadata = Column('metadata', JSONB)

    def __init__(self, *args, **kwargs):
        self._metadata = {}
        self.transport_params = {}
        # TODO SP: it's supposed to be nullable, but there is a NOT constraint inside the DB.
        self.description = ""

        super(DbComputer, self).__init__(*args, **kwargs)

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return '{} ({})'.format(self.name, self.hostname)
