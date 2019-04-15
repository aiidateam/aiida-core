# -*- coding: utf-8 -*-

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, DateTime, String

from aiida.utils import timezone
from aiida.backends.sqlalchemy.models.base import Base
from aiida.common.exceptions import ValidationError


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

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
