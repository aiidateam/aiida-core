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
from sqlalchemy.sql.schema import Index
from sqlalchemy.types import Integer, String

from aiida.storage.psql_dos.models.base import Base


class DbUser(Base):
    """Database model to store data for :py:class:`aiida.orm.User`.

    Every node that is created has a single user as its author.

    The user information consists of the most basic personal contact details.
    """
    __tablename__ = 'db_dbuser'

    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name
    email = Column(String(254), nullable=False, unique=True)
    first_name = Column(String(254), default='', nullable=False)
    last_name = Column(String(254), default='', nullable=False)
    institution = Column(String(254), default='', nullable=False)

    __table_args__ = (
        Index(
            'ix_pat_db_dbuser_email', email, postgresql_using='btree', postgresql_ops={'email': 'varchar_pattern_ops'}
        ),
    )

    def __str__(self):
        return self.email
