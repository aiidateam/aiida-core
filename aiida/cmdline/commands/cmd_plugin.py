# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Command for `verdi plugins`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import decorators, echo
from aiida.plugins.entry_point import entry_point_group_to_module_path_map


@verdi.group('plugin')
def verdi_plugin():
    """Inspect installed plugins for various entry point categories."""


@verdi_plugin.command('list')
@click.argument('entry_point_group', type=click.Choice(entry_point_group_to_module_path_map.keys()), required=False)
@click.argument('entry_point', type=click.STRING, required=False)
@decorators.with_dbenv()
def plugin_list(entry_point_group, entry_point):
    """Display a list of all available plugins."""
    from aiida.common.exceptions import LoadingPluginFailed, MissingPluginError
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
        except (LoadingPluginFailed, MissingPluginError) as exception:
            echo.echo_critical(exception)
        else:
            echo.echo_info(entry_point)
            try:
                echo.echo(plugin.get_description())
            except AttributeError:
                echo.echo('No description available')
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
