# -*- coding: utf-8 -*-
from pytz import UTC
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import Integer, String, DateTime

from aiida.backends.sqlalchemy import session
from aiida.backends.sqlalchemy.models.base import Base
from aiida.utils import timezone


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

class DbSetting(Base):
    __tablename__ = "db_dbsetting"
    __table_args__ = (UniqueConstraint('key'),)
    id = Column(Integer, primary_key=True)

    key = Column(String(255), index=True, nullable=False)
    val = Column(JSONB, default={})

    # I also add a description field for the variables
    description = Column(String(255), default='', nullable=False)
    time = Column(DateTime(timezone=True), default=timezone.utc)

    def __str__(self):
        return "'{}'={}".format(self.key, self.getvalue())
    
    @classmethod
    def set_value(cls, key, value, with_transaction=True,
                  subspecifier_value=None, other_attribs={},
                  stop_if_existing=False):

        setting = session.query(DbSetting).filter_by(key=key).first()
        if setting is not None:
            if stop_if_existing:
                return
        else:
            setting = cls()

        setting.key = key
        setting.val = value
        setting.time = timezone.datetime.now(tz=UTC)
        if "description" in other_attribs.keys():
            setting.description = other_attribs["description"]
        flag_modified(setting, "val")
        setting.save()

    def getvalue(self):
        """
        This can be called on a given row and will get the corresponding value.
        """
        return self.val

    def get_description(self):
        """
        This can be called on a given row and will get the corresponding
        description.
        """
        return self.description

    @classmethod
    def del_value(cls, key, only_children=False, subspecifier_value=None):
        setting = session.query(DbSetting).filter(key=key)
        setting.val = None
        setting.time = timezone.datetime.utcnow()
        flag_modified(setting, "val")
        setting.save()
