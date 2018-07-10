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
from aiida.cmdline.commands.data.list import _list, list_options
from aiida.cmdline.commands.data.export import _export, export_options
from aiida.cmdline.commands.data.deposit import deposit_tcod, deposit_options
from aiida.cmdline.utils import echo
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline.params import arguments

from aiida.orm.data.structure import StructureData


@verdi_data.group('cif')
@click.pass_context
def cif(ctx):
    """help"""
    pass

@cif.command('show')
@arguments.NODES()
@click.option('-f', '--format', 'given_format',
              type=click.Choice(['jmol', 'vesta']),
              default='jmol',
              help="Type of the visualization format/tool.")
def show(nodes, given_format):
    """
    Visualize CifData objects
    """
    from aiida.orm.data.cif import CifData
    from aiida.cmdline.commands.data.show import _show_jmol
    from aiida.cmdline.commands.data.show import _show_vesta

    for n in nodes:
        if not isinstance(n, CifData):
            echo.echo_critical("Node {} is of class {} instead "
                                "of {}".format(n, type(n), StructureData))
    if given_format == "jmol":
        _show_jmol(given_format, nodes)
    elif given_format == "vesta":
        _show_vesta(given_format, nodes)
    else:
        raise NotImplementedError ("The format {} is not yet implemented"
                                   .format(given_format))

project_headers = ["Id", "Formulae", "Source.URI"]
@cif.command('list')
@click.option('-f', '--formulamode',
              type=click.Choice(['hill', 'hill_compact', 'reduce', 'group', 'count', 'count_compact']),
              default='hill',
              help="Formula printing mode (if None, does not print the formula)")
@list_options
def cif_list(raw, formulamode, past_days, groups, all_users):
    """
    List store CifData objects
    """
    from aiida.orm.data.cif import CifData
    from tabulate import tabulate
    elements = None
    elements_only = False

    entry_list = _list(CifData, project_headers, elements,
                elements_only, formulamode, past_days,
                groups, all_users)

    counter = 0
    cif_list_data = list()

    if not raw:
        cif_list_data.append(project_headers)
    for entry in entry_list:
        for i in range(0, len(entry)):
            if isinstance(entry[i], list):
                new_entry = list()
                for e in entry[i]:
                    if e is None:
                        new_entry.append('')
                    else:
                        new_entry.append(e)
                entry[i] = ",".join(new_entry)
        for i in range(len(entry), len(project_headers)):
                entry.append(None)
        counter += 1
    cif_list_data.extend(entry_list)
    if raw:
        echo.echo(tabulate(cif_list_data, tablefmt='plain'))
    else:
        echo.echo(tabulate(cif_list_data, headers="firstrow"))
        echo.echo("\nTotal results: {}\n".format(counter))


supported_formats = ['cif', 'tcod']
@cif.command('export')
@click.option('-y', '--format',
              type=click.Choice(supported_formats),
              default='cif',
              help="Type of the exported file.")
@export_options
def export(**kwargs):
    """
    Export CifData object
    """
    from aiida.orm.data.cif import CifData

    node = kwargs.pop('node')
    output = kwargs.pop('output')
    format = kwargs.pop('format')
    force = kwargs.pop('force')

    for key,value in kwargs.items():
        if value is None:
            kwargs.pop(key)  

    if not isinstance(node, CifData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), CifData))
    _export(node, output, format, other_args=kwargs, overwrite=force)


@cif.command('import')
@click.option('-f', '--format',
              type=click.Choice(['cif']),
              default='cif',
              help="Type of the imported file.")
@click.argument('filename',
                type=click.Path(exists=True,
                    dir_okay=False,
                    resolve_path=True))
def importfile(format, filename):
    """
    Import structure into CifData object
    """
    import os
    from aiida.orm.data.cif import CifData

    try:
        node, _ = CifData.get_or_create(os.path.abspath(filename))
        echo.echo_success("imported {}".format(str(node)))
    except ValueError as e:
        echo.echo_critical(e)


@cif.command('deposit')
@deposit_options
def deposit(**kwargs):
    """
    Deposit CifData object
    """
    from aiida.orm.data.cif import CifData
    # if not is_dbenv_loaded():
    #     load_dbenv()
    node = kwargs.pop('node')
    deposition_type = kwargs.pop('deposition_type')
    parameter_data = kwargs.pop('parameter_data')

    #if kwargs['database'] is None:
        #echo.echo_critical("Default database is not defined, please specify.")
    kwargs.pop('database') # looks like a bug, but deposit function called inside deposit_tcod complains about the 'database' keywords argument
    
    for key,value in kwargs.items():
        if value is None:
            kwargs.pop(key) 

    if not isinstance(node, CifData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), CifData))
    echo.echo(deposit_tcod(node, deposition_type, parameter_data, **kwargs))

