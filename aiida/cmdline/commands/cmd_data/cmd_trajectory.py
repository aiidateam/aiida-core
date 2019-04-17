# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data trajectory` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from six.moves import range

import click

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.commands.cmd_data import cmd_show
from aiida.cmdline.commands.cmd_data.cmd_export import data_export, export_options
from aiida.cmdline.commands.cmd_data.cmd_list import data_list, list_options
from aiida.cmdline.commands.cmd_data.cmd_show import show_options
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo

LIST_PROJECT_HEADERS = ['Id', 'Label']
EXPORT_FORMATS = ['cif', 'xsf']
VISUALIZATION_FORMATS = ['jmol', 'xcrysden', 'mpl_heatmap', 'mpl_pos']


@verdi_data.group('trajectory')
def trajectory():
    """View and manipulate TrajectoryData instances."""


@trajectory.command('list')
@list_options
@decorators.with_dbenv()
def trajectory_list(raw, past_days, groups, all_users):
    """List trajectories stored in database."""
    from aiida.orm import TrajectoryData
    from tabulate import tabulate

    elements = None
    elements_only = False
    formulamode = None
    entry_list = data_list(TrajectoryData, LIST_PROJECT_HEADERS, elements, elements_only, formulamode, past_days,
                           groups, all_users)

    counter = 0
    struct_list_data = list()
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
        echo.echo('\nTotal results: {}\n'.format(counter))


@trajectory.command('show')
@arguments.DATA(type=types.DataParamType(sub_classes=('aiida.data:array.trajectory',)))
@options.VISUALIZATION_FORMAT(type=click.Choice(VISUALIZATION_FORMATS), default='jmol')
@show_options
@decorators.with_dbenv()
def trajectory_show(data, fmt):
    """Visualize trajectory."""
    try:
        show_function = getattr(cmd_show, '_show_{}'.format(fmt))
    except AttributeError:
        echo.echo_critical('visualization format {} is not supported'.format(fmt))

    show_function(fmt, data)


@trajectory.command('export')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:array.trajectory',)))
@options.EXPORT_FORMAT(type=click.Choice(EXPORT_FORMATS), default='cif')
@options.TRAJECTORY_INDEX()
@export_options
@decorators.with_dbenv()
def trajectory_export(**kwargs):
    """Export trajectory."""
    node = kwargs.pop('datum')
    output = kwargs.pop('output')
    fmt = kwargs.pop('fmt')
    force = kwargs.pop('force')

    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    data_export(node, output, fmt, other_args=kwargs, overwrite=force)
