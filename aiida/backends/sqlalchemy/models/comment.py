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
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from aiida.common import timezone
from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.utils import get_new_uuid


class DbComment(Base):
    __tablename__ = "db_dbcomment"

    id = Column(Integer, primary_key=True)

    uuid = Column(UUID(as_uuid=True), default=get_new_uuid, unique=True)
    dbnode_id = Column(
        Integer,
        ForeignKey(
            'db_dbnode.id', ondelete="CASCADE",
            deferrable=True, initially="DEFERRED"
        )
    )

    ctime = Column(DateTime(timezone=True), default=timezone.now)
    mtime = Column(DateTime(timezone=True), default=timezone.now, onupdate=timezone.now)

    user_id = Column(
        Integer,
        ForeignKey(
            'db_dbuser.id', ondelete="CASCADE",
            deferrable=True, initially="DEFERRED"
        )
    )
    content = Column(Text, nullable=True)

    dbnode = relationship('DbNode', backref='dbcomments')
    user = relationship("DbUser")

    def __str__(self):
        return "DbComment for [{} {}] on {}".format(
            self.dbnode.get_simple_name(),
            self.dbnode.id, timezone.localtime(self.ctime).strftime("%Y-%m-%d")
        )

    def __init__(self, *args, **kwargs):
        super(DbComment, self).__init__(*args, **kwargs)
        # The behavior of an unstored Comment instance should be that all its attributes should be initialized in
        # accordance with the defaults specified on the collums, i.e. if a default is specified for the `uuid` column,
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
