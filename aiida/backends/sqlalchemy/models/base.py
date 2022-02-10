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


Base = declarative_base(cls=Model, name='Model')  # pylint: disable=invalid-name


def get_orm_metadata() -> MetaData:
    """Return the populated metadata object."""
    # we must load all models, to populate the ORM metadata
    from aiida.backends.sqlalchemy.models import (  # pylint: disable=unused-import
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
