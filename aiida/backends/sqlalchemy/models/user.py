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
"""Module to manage users for the SQLA backend."""

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String

from aiida.backends.sqlalchemy.models.base import Base


class DbUser(Base):
    """Store users using the SQLA backend."""
    __tablename__ = 'db_dbuser'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    email = Column(String(254), unique=True, index=True)
    first_name = Column(String(254), nullable=True)
    last_name = Column(String(254), nullable=True)
    institution = Column(String(254), nullable=True)

    def __init__(self, email, first_name='', last_name='', institution='', **kwargs):
        """Set additional class attributes with respect to the base class."""
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.institution = institution
        super().__init__(**kwargs)

    def __str__(self):
        return self.email
