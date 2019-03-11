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
from __future__ import with_statement
from __future__ import absolute_import

from alembic import context
from aiida.backends.settings import IN_DOC_MODE

# The available SQLAlchemy tables
from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
from aiida.backends.sqlalchemy.models.comment import DbComment
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.backends.sqlalchemy.models.group import DbGroup
from aiida.backends.sqlalchemy.models.log import DbLog
from aiida.backends.sqlalchemy.models.node import DbComputer, DbLink, DbNode
from aiida.backends.sqlalchemy.models.settings import DbSetting
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.backends.sqlalchemy.models.workflow import DbWorkflow
from aiida.common.exceptions import DbContentError
from aiida.backends.sqlalchemy.models.base import Base
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    raise NotImplementedError("This feature is not currently supported.")


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # This is the Alembic Config object, which provides
    # access to the values within the .ini file in use.
    # It is initialized by alembic and we enrich it here
    # to point to the right database configuration.
    config = context.config

    connectable = config.attributes.get('connection', None)

    if connectable is None:
        from aiida.common.exceptions import ConfigurationError
        raise ConfigurationError("An initialized connection is expected "
                                 "for the AiiDA online migrations.")

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if not IN_DOC_MODE:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
