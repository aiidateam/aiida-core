# -*- coding: utf-8 -*-

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, DateTime, String

from aiida.utils import timezone
from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.exceptions import ValidationError



class DbLock(Base):
    __tablename__ = "db_dblock"

    key = Column(String(255), primary_key=True)
    creation = Column(DateTime(timezone=True), default=timezone.now)
    timeout = Column(Integer)
    owner = Column(String(255))

    def __init__(self, **kwargs):
        if 'owner' not in kwargs or not kwargs["owner"]:
            raise ValidationError("The field owner can't be empty")

        self.__init__(**kwargs)
