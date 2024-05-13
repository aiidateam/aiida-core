###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""``verdi presto`` command."""

from __future__ import annotations

import pathlib
import re
import typing as t

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo
from aiida.manage.configuration import get_config_option

DEFAULT_PROFILE_NAME_PREFIX: str = 'presto'


def get_default_presto_profile_name():
    from aiida.manage import get_config

    profile_names = get_config().profile_names
    indices = []

    for profile_name in profile_names:
        if match := re.search(r'presto[-]?(\d+)?', profile_name):
            indices.append(match.group(1) or '0')

    if not indices:
        return DEFAULT_PROFILE_NAME_PREFIX

    last_index = int(sorted(indices)[-1])

    return f'{DEFAULT_PROFILE_NAME_PREFIX}-{last_index + 1}'


@verdi.command('presto')
@click.option(
    '--profile-name',
    default=lambda: get_default_presto_profile_name(),
    show_default=True,
    help=f'Name of the profile. By default, a unique name starting with `{DEFAULT_PROFILE_NAME_PREFIX}` is '
    'automatically generated.',
)
@click.option(
    '--email',
    default=get_config_option('autofill.user.email') or 'aiida@localhost',
    show_default=True,
    help='Email of the default user.',
)
@click.pass_context
def verdi_presto(ctx, profile_name, email):
    """Set up a new profile in a jiffy.

    This command aims to make setting up a new profile as easy as possible. It intentionally provides only a limited
    amount of options to customize the profile and by default does not require any options to be specified at all. For
    full control, please use `verdi profile setup`.

    After running `verdi presto` you can immediately start using AiiDA without additional setup. The created profile
    uses the `core.sqlite_dos` storage plugin which does not require any services, such as PostgreSQL. The broker
    service RabbitMQ is also optional. The command tries to connect to it using default settings and configures it for
    the profile if found. Otherwise, the profile is created without a broker, in which case some functionality will be
    unavailable, most notably running the daemon and submitting processes to said daemon.

    The command performs the following actions:

    \b
    * Create a new profile that is set as the new default
    * Create a default user for the profile (email can be configured through the `--email` option)
    * Set up the localhost as a `Computer` and configure it
    * Set a number of configuration options with sensible defaults

    """
    from aiida.brokers.rabbitmq.defaults import detect_rabbitmq_config
    from aiida.common import exceptions
    from aiida.manage.configuration import create_profile, load_profile
    from aiida.orm import Computer

    storage_config: dict[str, t.Any] = {}
    storage_backend = 'core.sqlite_dos'

    broker_config = detect_rabbitmq_config()
    broker_backend = 'core.rabbitmq' if broker_config is not None else None

    if broker_config is None:
        echo.echo_report('RabbitMQ server not found: configuring the profile without a broker.')
    else:
        echo.echo_report('RabbitMQ server detected: configuring the profile with a broker.')

    try:
        profile = create_profile(
            ctx.obj.config,
            name=profile_name,
            email=email,
            storage_backend=storage_backend,
            storage_config=storage_config,
            broker_backend=broker_backend,
            broker_config=broker_config,
        )
    except (ValueError, TypeError, exceptions.EntryPointError, exceptions.StorageMigrationError) as exception:
        echo.echo_critical(str(exception))

    echo.echo_success(f'Created new profile `{profile.name}`.')

    ctx.obj.config.set_option('runner.poll.interval', 1, scope=profile.name)
    ctx.obj.config.set_default_profile(profile.name, overwrite=True)
    ctx.obj.config.store()

    load_profile(profile.name, allow_switch=True)
    echo.echo_info(f'Loaded newly created profile `{profile.name}`.')

    filepath_scratch = pathlib.Path(ctx.obj.config.dirpath) / 'scratch' / profile.name

    computer = Computer(
        label='localhost',
        hostname='localhost',
        description='Localhost automatically created by `verdi presto`',
        transport_type='core.local',
        scheduler_type='core.direct',
        workdir=str(filepath_scratch),
    ).store()
    computer.configure(safe_interval=0)
    computer.set_minimum_job_poll_interval(1)
    computer.set_default_mpiprocs_per_machine(1)

    echo.echo_success('Configured the localhost as a computer.')
