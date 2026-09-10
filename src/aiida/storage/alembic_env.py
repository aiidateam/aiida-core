###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
###########################################################################
"""Shared Alembic environment for AiiDA storage migration graphs."""

from alembic import context


def run_migrations_online() -> None:
    """Run migrations using the connection supplied by :class:`AlembicMigrator`."""
    config = context.config
    connection = config.attributes.get('connection')
    target_metadata = config.attributes.get('target_metadata')

    if connection is None:
        from aiida.common.exceptions import ConfigurationError

        raise ConfigurationError('An initialized connection is expected for the AiiDA online migrations.')
    if target_metadata is None:
        from aiida.common.exceptions import ConfigurationError

        raise ConfigurationError('Target metadata is expected for the AiiDA online migrations.')

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        transaction_per_migration=True,
        aiida_profile=config.attributes.get('aiida_profile'),
        on_version_apply=config.attributes.get('on_version_apply'),
    )
    context.run_migrations()


def run() -> None:
    """Execute the Alembic environment, rejecting offline migrations."""
    try:
        if context.is_offline_mode():
            raise NotImplementedError('This feature is not currently supported.')
        run_migrations_online()
    except NameError:
        # This occurs when the documentation builder compiles migration modules.
        pass
