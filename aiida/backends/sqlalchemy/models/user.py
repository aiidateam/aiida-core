# -*- coding: utf-8 -*-

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from aiida.utils import timezone
from aiida.backends.sqlalchemy.models.base import Base


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"


class DbUser(Base):
    __tablename__ = "db_dbuser"

    id = Column(Integer, primary_key=True)
    email = Column(String(254), unique=True, index=True)
    password = Column(String(128))  # Clear text password ?

    # Not in django model definition, but comes from inheritance?
    is_superuser = Column(Boolean, default=False, nullable=False)

    first_name = Column(String(254), nullable=True)
    last_name = Column(String(254), nullable=True)
    institution = Column(String(254), nullable=True)

    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)

    last_login = Column(DateTime(timezone=True), default=timezone.now)
    date_joined = Column(DateTime(timezone=True), default=timezone.now)

    dbnodes_q = relationship(
            'DbNode',
            lazy='dynamic'
        )

    # XXX is it safe to set name and institution to an empty string ?
    def __init__(self, email, first_name="", last_name="", institution="", **kwargs):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.institution = institution
        super(DbUser, self).__init__(**kwargs)

    def get_full_name(self):
        if self.first_name and self.last_name:
            return "{} {} ({})".format(self.first_name, self.last_name,
                                       self.email)
        elif self.first_name:
            return "{} ({})".format(self.first_name, self.email)
        elif self.last_name:
            return "{} ({})".format(self.last_name, self.email)
        else:
            return "{}".format(self.email)

    def get_short_name(self):
        return self.email

    def __str__(self):
        return self.email

    def get_aiida_class(self):
        from aiida.orm.user import User
        return User(dbuser=self)

