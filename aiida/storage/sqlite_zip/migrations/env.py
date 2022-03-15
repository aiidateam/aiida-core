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
    from aiida.storage.sqlite_zip.models import SqliteBase

    config = context.config  # pylint: disable=no-member

    connection = config.attributes.get('connection', None)
    aiida_profile = config.attributes.get('aiida_profile', None)
    on_version_apply = config.attributes.get('on_version_apply', None)

    if connection is None:
        from aiida.common.exceptions import ConfigurationError
        raise ConfigurationError('An initialized connection is expected for the AiiDA online migrations.')

    context.configure(  # pylint: disable=no-member
        connection=connection,
        target_metadata=SqliteBase.metadata,
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
