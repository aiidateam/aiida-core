# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import click

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import verdi, verdi_data
from aiida.cmdline.utils import decorators, echo


class Data(VerdiCommandWithSubcommands):
    """
    Setup and manage data specific types

    There is a list of subcommands for managing specific types of data.
    For instance, 'data upf' manages pseudopotentials in the UPF format.
    """

    def __init__(self):
        super(Data, self).__init__()

        # import to populate the click subcommands
        from aiida.cmdline.commands.data import (
            upf,
            structure,
            bands,
            cif,
            trajectory,
            parameter,
            array,
            remote,
            )

        self.valid_subcommands = {
            'upf': (self.cli, self.complete_none),
            'structure': (self.cli, self.complete_none),
            'bands': (self.cli, self.complete_none),
            'cif': (self.cli, self.complete_none),
            'trajectory': (self.cli, self.complete_none),
            'parameter': (self.cli, self.complete_none),
            'array': (self.cli, self.complete_none),
            'remote': (self.cli, self.complete_none),
            'plugins': (self.cli, self.complete_plugins),
        }

    @staticmethod
    def cli(*args):  # pylint: disable=unused-argument
        verdi()  # pylint: disable=no-value-for-parameter

    @staticmethod
    @decorators.with_dbenv()
    def complete_plugins(subargs_idx, subargs):
        """Return the list of plugins registered under the 'data' category."""
        from aiida.plugins.entry_point import get_entry_point_names

        other_subargs = subargs[:subargs_idx] + subargs[subargs_idx + 1:]
        return_plugins = [e for e in get_entry_point_names('aiida.data') if e not in other_subargs]
        return '\n'.join(return_plugins)


@verdi_data.command('plugins')
@click.argument('entry_point', type=click.STRING, required=False)
@decorators.with_dbenv()
def data_plugins(entry_point):
    """
    Print a list of registered data plugins or details of a specific data plugin
    """
    from aiida.common.exceptions import LoadingPluginFailed, MissingPluginError
    from aiida.plugins.entry_point import get_entry_point_names, load_entry_point

    if entry_point:
        try:
            plugin = load_entry_point('aiida.data', entry_point)
        except (LoadingPluginFailed, MissingPluginError) as exception:
            echo.echo_critical(exception)
        else:
            echo.echo_info(entry_point)
            echo.echo(plugin.get_description())
    else:
        entry_points = get_entry_point_names('aiida.data')
        if entry_points:
            echo.echo('Registered data entry points:')
            for entry_point in entry_points:
                echo.echo("* {}".format(entry_point))

            echo.echo('')
            echo.echo_info('Pass the entry point as an argument to display detailed information')
        else:
            echo.echo_error('No data plugins found')
