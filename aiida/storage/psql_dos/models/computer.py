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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.schema import Column
from sqlalchemy.sql.schema import Index
from sqlalchemy.types import Integer, String, Text

from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.models.base import Base


class DbComputer(Base):
    """Database model to store data for :py:class:`aiida.orm.Computer`.

    Computers represent (and contain the information of) the physical hardware resources available.
    Nodes can be associated with computers if they are remote codes, remote folders, or processes that had run remotely.

    Computers are identified within AiiDA by their ``label`` (and thus it must be unique for each one in the database),
    whereas the ``hostname`` is the label that identifies the computer within the network from which one can access it.

    The ``scheduler_type`` column contains the information of the scheduler (and plugin)
    that the computer uses to manage jobs, whereas the ``transport_type`` the information of the transport
    (and plugin) required to copy files and communicate to and from the computer.
    The ``metadata`` contains some general settings for these communication and management protocols.
    """
    __tablename__ = 'db_dbcomputer'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, nullable=False, unique=True)
    label = Column(String(255), nullable=False, unique=True)
    hostname = Column(String(255), default='', nullable=False)
    description = Column(Text, default='', nullable=False)
    scheduler_type = Column(String(255), default='', nullable=False)
    transport_type = Column(String(255), default='', nullable=False)
    _metadata = Column('metadata', JSONB, default=dict, nullable=False)

    __table_args__ = (
        Index(
            'ix_pat_db_dbcomputer_label',
            label,
            postgresql_using='btree',
            postgresql_ops={'label': 'varchar_pattern_ops'}
        ),
    )

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return f'{self.label} ({self.hostname})'
