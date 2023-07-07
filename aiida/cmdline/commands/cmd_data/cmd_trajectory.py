# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data core.trajectory` command."""

import click

from aiida.cmdline.commands.cmd_data import cmd_show, verdi_data
from aiida.cmdline.commands.cmd_data.cmd_export import data_export, export_options
from aiida.cmdline.commands.cmd_data.cmd_list import data_list, list_options
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo

LIST_PROJECT_HEADERS = ['Id', 'Label']
EXPORT_FORMATS = ['cif', 'xsf']
VISUALIZATION_FORMATS = ['jmol', 'xcrysden', 'mpl_heatmap', 'mpl_pos']


@verdi_data.group('core.trajectory')
def trajectory():
    """Manipulate TrajectoryData objects (molecular trajectories)."""


@trajectory.command('list')
@list_options
@decorators.with_dbenv()
def trajectory_list(raw, past_days, groups, all_users):
    """List TrajectoryData objects stored in the database."""
    from tabulate import tabulate

    from aiida.orm import TrajectoryData

    elements = None
    elements_only = False
    formulamode = None
    entry_list = data_list(
        TrajectoryData, LIST_PROJECT_HEADERS, elements, elements_only, formulamode, past_days, groups, all_users
    )

    counter = 0
    struct_list_data = []
    if not raw:
        struct_list_data.append(LIST_PROJECT_HEADERS)
    for entry in entry_list:
        for i, value in enumerate(entry):
            if isinstance(value, list):
                entry[i] = ','.join(value)
        for i in range(len(entry), len(LIST_PROJECT_HEADERS)):
            entry.append(None)
        counter += 1
    struct_list_data.extend(entry_list)
    if raw:
        echo.echo(tabulate(struct_list_data, tablefmt='plain'))
    else:
        echo.echo(tabulate(struct_list_data, headers='firstrow'))
        echo.echo(f'\nTotal results: {counter}\n')


@trajectory.command('show')
@arguments.DATA(type=types.DataParamType(sub_classes=('aiida.data:core.array.trajectory',)))
@options.VISUALIZATION_FORMAT(type=click.Choice(VISUALIZATION_FORMATS), default='jmol')
@options.TRAJECTORY_INDEX()
@options.WITH_ELEMENTS()
@click.option(
    '-c', '--contour', type=click.FLOAT, cls=options.MultipleValueOption, default=None, help='Isovalues to plot'
)
@click.option(
    '--sampling-stepsize',
    type=click.INT,
    default=None,
    help='Sample positions in plot every sampling_stepsize timestep'
)
@click.option(
    '--stepsize',
    type=click.INT,
    default=None,
    help='The stepsize for the trajectory, set it higher to reduce number of points'
)
@click.option('--mintime', type=click.INT, default=None, help='The time to plot from')
@click.option('--maxtime', type=click.INT, default=None, help='The time to plot to')
@click.option(
    '--indices', type=click.INT, cls=options.MultipleValueOption, default=None, help='Show only these indices'
)
@click.option('--dont-block', 'block', is_flag=True, default=True, help="Don't block interpreter when showing plot.")
@decorators.with_dbenv()
def trajectory_show(data, fmt, **kwargs):
    """Visualize a trajectory."""
    try:
        show_function = getattr(cmd_show, f'_show_{fmt}')
    except AttributeError:
        echo.echo_critical(f'visualization format {fmt} is not supported')

    show_function(exec_name=fmt, trajectory_list=data, **kwargs)


@trajectory.command('export')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:core.array.trajectory',)))
@options.EXPORT_FORMAT(type=click.Choice(EXPORT_FORMATS), default='cif')
@options.TRAJECTORY_INDEX()
@export_options
@decorators.with_dbenv()
def trajectory_export(**kwargs):
    """Export trajectory to file."""
    node = kwargs.pop('datum')
    output = kwargs.pop('output')
    fmt = kwargs.pop('fmt')
    force = kwargs.pop('force')

    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    data_export(node, output, fmt, other_args=kwargs, overwrite=force)
