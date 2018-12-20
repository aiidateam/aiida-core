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
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Boolean, DateTime
from aiida.common import timezone
from aiida.backends.sqlalchemy.models.base import Base


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

    # XXX is it safe to set name and institution to an empty string ?
    def __init__(self, email, first_name="", last_name="", institution="", **kwargs):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.institution = institution
        super(DbUser, self).__init__(**kwargs)

    def __str__(self):
        return self.email
