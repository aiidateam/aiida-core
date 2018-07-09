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
from aiida.cmdline.commands import verdi_data
from aiida.cmdline.commands.data.export import _export, export_options
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.commands.data.list import _list, list_options
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline.commands.data.show import show_options
from aiida.cmdline.commands.data.deposit import deposit_options, deposit_tcod



        
@verdi_data.group('trajectory')
@click.pass_context
def trajectory(ctx):
    """
    View and manipulate TrajectoryData instances.
    """
    pass

project_headers = ["Id", "Label"]
@trajectory.command('list')
@list_options
def list_trajections(raw, formulamode, past_days, groups, all_users):
    """
    List trajectories stored in database.
    """
    from aiida.orm.data.array.trajectory import TrajectoryData
    from tabulate import tabulate
    elements = None
    elements_only = False
    entry_list = _list(TrajectoryData, project_headers, elements, elements_only, formulamode, past_days, groups, all_users)

    counter = 0
    struct_list_data = list()
    if not raw:
        struct_list_data.append(project_headers)
    for entry in entry_list:
        for i in range(0, len(entry)):
            if isinstance(entry[i], list):
                entry[i] = ",".join(entry[i])
        for i in range(len(entry), len(project_headers)):
                entry.append(None)
        counter += 1
    struct_list_data.extend(entry_list)
    if raw:
        echo.echo(tabulate(struct_list_data, tablefmt='plain'))
    else:
        echo.echo(tabulate(struct_list_data, headers="firstrow"))
        echo.echo("\nTotal results: {}\n".format(counter))


@trajectory.command('show')
@show_options
def show (**kwargs):
    """
    Visualize trajectory
    """
    from aiida.orm.data.array.trajectory import TrajectoryData
    from aiida.cmdline.commands.data.show import _show_jmol
    from aiida.cmdline.commands.data.show import _show_xcrysden
    from aiida.cmdline.commands.data.show import _show_mpl_pos
    from aiida.cmdline.commands.data.show import _show_mpl_heatmap
    nodes = kwargs.pop('nodes')
    given_format = kwargs.pop('format')
    for n in nodes:
        if not isinstance(n, TrajectoryData):
            echo.echo_critical("Node {} is of class {} instead "
                                "of {}".format(n, type(n), TrajectoryData))
            
    for key,value in kwargs.items():
        if value is None:
            kwargs.pop(key)

    if given_format == "jmol":
        _show_jmol(given_format, nodes, **kwargs)
    elif given_format == "xcrysden":
        _show_xcrysden(given_format, nodes, **kwargs)
    elif given_format == "mpl_pos":
        _show_mpl_pos(given_format, nodes, **kwargs)
    elif given_format == "mpl_heatmap":
        _show_mpl_heatmap(given_format, nodes, **kwargs)
    else:
        raise NotImplementedError ("The format {} is not yet implemented"
                                   .format(given_format))


@trajectory.command('export')
@click.option('-y', '--format',
              type=click.Choice(['cif', 'tcod', 'xsf']),
              default='cif',
              help="Type of the exported file.")
@click.option('--step', type=click.INT,
              default=None,
              help="ID of the trajectory step. If none is supplied, all"
              " steps are explored.")
@export_options
def export(**kwargs):
    """
    Export trajectory
    """
    from aiida.orm.data.array.trajectory import TrajectoryData

    node = kwargs.pop('node')
    output = kwargs.pop('output')
    format = kwargs.pop('format')
    force = kwargs.pop('force')
    
    for key,value in kwargs.items():
        if value is None:
            kwargs.pop(key)    

    if not isinstance(node, TrajectoryData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), TrajectoryData))
    _export(node, output, format, other_args=kwargs, overwrite=force)


@trajectory.command('deposit')
@click.option('--step','trajectory_index', type=click.INT,
             default=1,
             help="ID of the trajectory step. If none is "
             "supplied, all steps are exported.")
@deposit_options
def deposit(**kwargs):
    """
    Deposit trajectory object
    """
    from aiida.orm.data.array.trajectory import TrajectoryData
    if not is_dbenv_loaded():
        load_dbenv()
    node = kwargs.pop('node')
    deposition_type = kwargs.pop('deposition_type')
    parameter_data = kwargs.pop('parameter_data')

    if kwargs['database'] is None:
        echo.echo_critical("Default database is not defined, please specify.")

    for key,value in kwargs.items():
        if value is None:
            kwargs.pop(key) 
    
    if not isinstance(node, TrajectoryData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), TrajectoryData))
    calc = deposit_tcod(node, deposition_type, parameter_data, **kwargs)
