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
from sqlalchemy.sql.schema import Index, UniqueConstraint
from sqlalchemy.types import Integer, String

from aiida.backends.sqlalchemy.models.base import Base


class DbUser(Base):
    """Database model to store users.

    The user information consists of the most basic personal contact details.
    """
    __tablename__ = 'db_dbuser'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    email = Column(String(254), nullable=False)
    first_name = Column(String(254), default='', nullable=False)
    last_name = Column(String(254), default='', nullable=False)
    institution = Column(String(254), default='', nullable=False)

    __table_args__ = (
        # index/constraint names mirror django's auto-generated ones
        UniqueConstraint(email, name='db_dbuser_email_30150b7e_uniq'),
        Index(
            'db_dbuser_email_30150b7e_like',
            email,
            postgresql_using='btree',
            postgresql_ops={'email': 'varchar_pattern_ops'}
        ),
    )

    def __init__(self, email, first_name='', last_name='', institution='', **kwargs):
        """Set additional class attributes with respect to the base class."""
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.institution = institution
        super().__init__(**kwargs)

    def __str__(self):
        return self.email