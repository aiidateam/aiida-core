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

    def __init__(self, *args, **kwargs):
        """Adding mtime attribute if not present."""
        super().__init__(*args, **kwargs)
        # The behavior of an unstored Comment instance should be that all its attributes should be initialized in
        # accordance with the defaults specified on the columns, i.e. if a default is specified for the `uuid` column,
        # then an unstored `DbComment` instance should have a default value for the `uuid` attribute. The exception here
        # is the `mtime`, that we do not want to be set upon instantiation, but only upon storing. However, in
        # SqlAlchemy a default *has* to be defined if one wants to get that value upon storing. But since defining a
        # default on the column in combination with the hack in `aiida.backend.SqlAlchemy.models.__init__` to force all
        # defaults to be populated upon instantiation, we have to unset the `mtime` attribute here manually.
        #
        # The only time that we allow mtime not to be null is when we explicitly pass mtime as a kwarg. This covers
        # the case that a node is constructed based on some very predefined data like when we create nodes at the
        # AiiDA import functions.
        if 'mtime' not in kwargs:
            self.mtime = None
