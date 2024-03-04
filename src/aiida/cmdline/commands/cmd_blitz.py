###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi blitz` command."""
from __future__ import annotations

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo


@verdi.command('blitz')
@click.pass_context
def verdi_blitz(ctx):
    """Set up a minimal ready-to-go version of AiiDA.

    This command will create a profile that does not require any services like PostgreSQL and RabbitMQ. This makes it
    very easy to set up and get started using AiiDA. However, it will not provide all of AiiDA's functionality. The
    data storage is not designed for high-throughput and production use, and processes can only be run locally and not
    submitted to the daemon to allow AiiDA to scale with higher load.
    """
    import pathlib
    import tempfile

    from aiida.brokers.no_comms import NoCommsBroker
    from aiida.common import exceptions
    from aiida.manage.configuration import create_profile, load_profile
    from aiida.orm import Computer
    from aiida.storage.sqlite_dos import SqliteDosStorage

    profile_name = 'blitz'

    try:
        profile = create_profile(
            ctx.obj.config,
            name=profile_name,
            email='aiida@localhost',
            storage_cls=SqliteDosStorage,
            broker_cls=NoCommsBroker,
            broker_config={},
        )
    except (ValueError, TypeError, exceptions.EntryPointError, exceptions.StorageMigrationError) as exception:
        echo.echo_critical(str(exception))

    echo.echo_success(f'Created new profile `{profile.name}`.')

    ctx.obj.config.set_option('runner.poll.interval', 1, scope=profile_name)
    ctx.obj.config.set_default_profile(profile_name, overwrite=True)
    ctx.obj.config.store()

    echo.echo_info(f'Loaded newly created profile `{profile_name}`.')
    load_profile(profile_name, allow_switch=True)

    computer = Computer(
        label='localhost',
        hostname='localhost',
        description='Localhost automatically created by `verdi blitz`',
        transport_type='core.local',
        scheduler_type='core.direct',
        workdir=str(pathlib.Path(tempfile.gettempdir()) / 'aiida_scratch'),
    ).store()
    computer.configure(safe_interval=0.0)
    computer.set_minimum_job_poll_interval(0.0)
    computer.set_default_mpiprocs_per_machine(1)

    echo.echo_success('Configured the localhost as a computer.')
