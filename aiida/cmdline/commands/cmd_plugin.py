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

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import decorators, echo
from aiida.plugins.entry_point import entry_point_group_to_module_path_map


@verdi.group('plugin')
def verdi_plugin():
    """Inspect AiiDA plugins."""


@verdi_plugin.command('list')
@click.argument('entry_point_group', type=click.Choice(entry_point_group_to_module_path_map.keys()), required=False)
@click.argument('entry_point', type=click.STRING, required=False)
@decorators.with_dbenv()
def plugin_list(entry_point_group, entry_point):
    """Display a list of all available plugins."""
    from aiida.common import EntryPointError
    from aiida.cmdline.utils.common import print_process_info
    from aiida.engine import Process
    from aiida.plugins.entry_point import get_entry_point_names, load_entry_point

    if entry_point_group is None:
        echo.echo_info('Available entry point groups:')
        for group in sorted(entry_point_group_to_module_path_map.keys()):
            echo.echo('* {}'.format(group))

        echo.echo('')
        echo.echo_info('Pass one of the groups as an additional argument to show the registered plugins')
        return

    if entry_point:
        try:
            plugin = load_entry_point(entry_point_group, entry_point)
        except EntryPointError as exception:
            echo.echo_critical(str(exception))
        else:
            try:
                if issubclass(plugin, Process):
                    print_process_info(plugin)
                else:
                    echo.echo(str(plugin.get_description()))
            except (AttributeError, TypeError):
                echo.echo_error('No description available for {}'.format(entry_point))
    else:
        entry_points = get_entry_point_names(entry_point_group)
        if entry_points:
            echo.echo('Registered entry points for {}:'.format(entry_point_group))
            for registered_entry_point in entry_points:
                echo.echo('* {}'.format(registered_entry_point))

            echo.echo('')
            echo.echo_info('Pass the entry point as an argument to display detailed information')
        else:
            echo.echo_error('No plugins found for group {}'.format(entry_point_group))
