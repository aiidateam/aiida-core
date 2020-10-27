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
"""Module to manage computers for the SQLA backend."""
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Text

from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.utils import get_new_uuid


class DbComputer(Base):
    """Class to store computers using SQLA backend."""
    __tablename__ = 'db_dbcomputer'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, unique=True)
    name = Column(String(255), unique=True, nullable=False)
    hostname = Column(String(255))
    description = Column(Text, nullable=True)
    scheduler_type = Column(String(255))
    transport_type = Column(String(255))
    _metadata = Column('metadata', JSONB)

    def __init__(self, *args, **kwargs):
        """Provide _metadata and description attributes to the class."""
        self._metadata = {}
        self.description = ''

        # If someone passes metadata in **kwargs we change it to _metadata
        if 'metadata' in kwargs.keys():
            kwargs['_metadata'] = kwargs.pop('metadata')

        super().__init__(*args, **kwargs)

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return f'{self.name} ({self.hostname})'
