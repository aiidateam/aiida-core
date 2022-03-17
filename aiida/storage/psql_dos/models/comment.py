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
"""Module to manage comments for the SQLA backend."""
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import DateTime, Integer, Text

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.models.base import Base


class DbComment(Base):
    """Database model to store data for :py:class:`aiida.orm.Comment`.

    Comments can be attach to the nodes by the users.
    """

    __tablename__ = 'db_dbcomment'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, nullable=False, unique=True)
    dbnode_id = Column(
        Integer,
        ForeignKey('db_dbnode.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
        nullable=False,
        index=True
    )
    ctime = Column(DateTime(timezone=True), default=timezone.now, nullable=False)
    mtime = Column(DateTime(timezone=True), default=timezone.now, onupdate=timezone.now, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey('db_dbuser.id', ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
        nullable=False,
        index=True
    )
    content = Column(Text, default='', nullable=False)

    dbnode = relationship('DbNode', backref='dbcomments')
    user = relationship('DbUser')

    def __str__(self):
        return 'DbComment for [{} {}] on {}'.format(
            self.dbnode.get_simple_name(), self.dbnode.id,
            timezone.localtime(self.ctime).strftime('%Y-%m-%d')
        )
