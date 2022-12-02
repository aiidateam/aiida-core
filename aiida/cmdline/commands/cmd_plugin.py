# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Command for `verdi plugins`."""
import inspect

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import decorators, echo
from aiida.plugins.entry_point import ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP


@verdi.group('plugin')
def verdi_plugin():
    """Inspect AiiDA plugins."""


@verdi_plugin.command('list')
@click.argument('entry_point_group', type=click.Choice(list(ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP)), required=False)
@click.argument('entry_point', type=click.STRING, required=False)
@decorators.with_dbenv()
def plugin_list(entry_point_group, entry_point):
    """Display a list of all available plugins."""
    from aiida.cmdline.utils.common import print_process_info
    from aiida.common import EntryPointError
    from aiida.engine import Process
    from aiida.plugins.entry_point import get_entry_point_names, load_entry_point

    if entry_point_group is None:
        echo.echo_report('Available entry point groups:')
        for group in sorted(ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP.keys()):
            echo.echo(f'* {group}')

        echo.echo('')
        echo.echo_report('Pass one of the groups as an additional argument to show the registered plugins')
        return

    if entry_point:
        try:
            plugin = load_entry_point(entry_point_group, entry_point)
        except EntryPointError as exception:
            echo.echo_critical(str(exception))
        else:
            try:
                if (inspect.isclass(plugin) and issubclass(plugin, Process)) or plugin.is_process_function:
                    print_process_info(plugin)
                else:
                    echo.echo(str(plugin.get_description()))
            except AttributeError:
                echo.echo_error(f'No description available for {entry_point}')
    else:
        entry_points = get_entry_point_names(entry_point_group)
        if entry_points:
            echo.echo(f'Registered entry points for {entry_point_group}:')
            for registered_entry_point in entry_points:
                echo.echo(f'* {registered_entry_point}')

            echo.echo('')
            echo.echo_report('Pass the entry point as an argument to display detailed information')
        else:
            echo.echo_error(f'No plugins found for group {entry_point_group}')
