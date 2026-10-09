###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The `verdi data` command line interface."""

import typing as t

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.groups.dynamic import DynamicEntryPointCommandGroup
from aiida.cmdline.utils import echo
from aiida.cmdline.utils.pluginable import Pluginable
from aiida.common import exceptions


@verdi.group('data', entry_point_group='aiida.cmdline.data', cls=Pluginable)
def verdi_data():
    """Inspect, create and manage data nodes."""


def create_data(ctx: click.Context, cls: type[t.Any], model: t.Any) -> None:
    """Create and store a data node from its creation model."""
    try:
        instance = model.to_entity()
    except (TypeError, ValueError) as exception:
        echo.echo_critical(f'Failed to create instance `{cls}`: {exception}')

    try:
        instance.store()
    except exceptions.ValidationError as exception:
        echo.echo_critical(f'Failed to store instance of `{cls}`: {exception}')

    echo.echo_success(f'Created {cls.__name__}<{instance.pk}>')


@verdi_data.group(
    'create',
    cls=DynamicEntryPointCommandGroup,
    command=create_data,
    entry_point_group='aiida.data',
)
def data_create():
    """Create a data node from an entry point."""
