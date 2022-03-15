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
"""Base SQLAlchemy models."""
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base


class Model:
    """Base ORM model."""


# see https://alembic.sqlalchemy.org/en/latest/naming.html
naming_convention = (
    ('pk', '%(table_name)s_pkey'),  # this is identical to the default PSQL convention
    ('ix', 'ix_%(table_name)s_%(column_0_N_label)s'),
    # note, indexes using varchar_pattern_ops should be named: 'ix_pat_%(table_name)s_%(column_0_N_label)s'
    ('uq', 'uq_%(table_name)s_%(column_0_N_name)s'),
    ('ck', 'ck_%(table_name)s_%(constraint_name)s'),
    ('fk', 'fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s'),
    # note, ideally we may also append with '_%(referred_column_0_N_name)s', but this causes ORM construction errors:
    # https://github.com/sqlalchemy/sqlalchemy/issues/5350
)

Base = declarative_base(cls=Model, name='Model', metadata=MetaData(naming_convention=dict(naming_convention)))  # pylint: disable=invalid-name


def get_orm_metadata() -> MetaData:
    """Return the populated metadata object."""
    # we must load all models, to populate the ORM metadata
    from aiida.storage.psql_dos.models import (  # pylint: disable=unused-import
        authinfo,
        comment,
        computer,
        group,
        log,
        node,
        settings,
        user,
    )
    return Base.metadata
