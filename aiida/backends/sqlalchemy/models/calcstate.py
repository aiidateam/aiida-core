# -*- coding: utf-8 -*-

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, UniqueConstraint
from sqlalchemy.types import Integer, DateTime

from sqlalchemy_utils.types.choice import ChoiceType

from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.datastructures import calc_states
from aiida.utils import timezone

class DbCalcState(Base):
    __tablename__ = "db_dbcalcstate"

    id = Column(Integer, primary_key=True)

    dbnode_id = Column(Integer, ForeignKey('db_dbnode.id', ondelete="CASCADE"))
    dbnode = relationship('DbNode', backref='dbstates')

    state = Column(ChoiceType((_, _) for _ in calc_states), index=True)

    time = Column(DateTime(timezone=True), default=timezone.now)

    __table_args__ = (
        UniqueConstraint('dbnode_id', 'state'),
    )
