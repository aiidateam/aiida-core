# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Upper level SQLAlchemy migration funcitons."""
from alembic import context


def run_migrations_online():
    """Run migrations in 'online' mode.

    The connection should have been passed to the config, which we use to configue the migration context.
    """

    # pylint: disable=unused-import
    from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
    from aiida.backends.sqlalchemy.models.base import Base
    from aiida.backends.sqlalchemy.models.comment import DbComment
    from aiida.backends.sqlalchemy.models.computer import DbComputer
    from aiida.backends.sqlalchemy.models.group import DbGroup
    from aiida.backends.sqlalchemy.models.log import DbLog
    from aiida.backends.sqlalchemy.models.node import DbLink, DbNode
    from aiida.backends.sqlalchemy.models.settings import DbSetting
    from aiida.backends.sqlalchemy.models.user import DbUser
    from aiida.common.exceptions import DbContentError
    config = context.config  # pylint: disable=no-member

    connection = config.attributes.get('connection', None)
    aiida_profile = config.attributes.get('aiida_profile', None)
    on_version_apply = config.attributes.get('on_version_apply', None)

    if connection is None:
        from aiida.common.exceptions import ConfigurationError
        raise ConfigurationError('An initialized connection is expected for the AiiDA online migrations.')
    if aiida_profile is None:
        from aiida.common.exceptions import ConfigurationError
        raise ConfigurationError('An aiida_profile is expected for the AiiDA online migrations.')

    context.configure(  # pylint: disable=no-member
        connection=connection,
        target_metadata=Base.metadata,
        transaction_per_migration=True,
        aiida_profile=aiida_profile,
        on_version_apply=on_version_apply
    )

    context.run_migrations()  # pylint: disable=no-member


try:
    if context.is_offline_mode():  # pylint: disable=no-member
        NotImplementedError('This feature is not currently supported.')

    run_migrations_online()
except NameError:
    # This will occur in an environment that is just compiling the documentation
    pass
