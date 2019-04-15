# -*- coding: utf-8 -*-

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Column, UniqueConstraint
from sqlalchemy.types import Integer, DateTime

from sqlalchemy_utils.types.choice import ChoiceType

from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.datastructures import calc_states
from aiida.utils import timezone

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

class DbCalcState(Base):
    __tablename__ = "db_dbcalcstate"

    id = Column(Integer, primary_key=True)

    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    dbnode = relationship('DbNode', backref=backref('dbstates', passive_deletes=True))

    state = Column(ChoiceType((_, _) for _ in calc_states), index=True)

    time = Column(DateTime(timezone=True), default=timezone.now)

    __table_args__ = (
        UniqueConstraint('dbnode_id', 'state'),
    )
