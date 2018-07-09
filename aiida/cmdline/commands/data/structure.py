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
from aiida.cmdline.commands.data.list import _list, list_options
from aiida.cmdline.commands.data.export import _export, export_options
from aiida.cmdline.commands.data.deposit import deposit_tcod, deposit_options
from aiida.cmdline.commands import verdi_data
from aiida.cmdline.params import arguments
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline.utils import echo

@verdi_data.group('structure')
@click.pass_context
def structure(ctx):
    """
    Manipulation of the structures
    """
    pass
    

@structure.command('show')
@arguments.NODES()
@click.option('-f', '--format', 'given_format',
              type=click.Choice(['ase', 'jmol', 'vesta', 'vmd', 'xcrysden']),
              default='ase',
              help="Type of the visualization format/tool")
def show(nodes, given_format):
    """
    Visualize StructureData objects
    """
    from aiida.cmdline.commands.data.show import _show_jmol
    from aiida.cmdline.commands.data.show import _show_ase
    from aiida.cmdline.commands.data.show import _show_vesta
    from aiida.cmdline.commands.data.show import _show_vmd
    from aiida.cmdline.commands.data.show import _show_xcrysden
    from aiida.orm.data.structure import StructureData
    for n in nodes:
        if not isinstance(n, StructureData):
            echo.echo_critical("Node {} is of class {} instead "
                                "of {}".format(n, type(n), StructureData))
    if given_format == "ase":
        _show_ase(given_format, nodes)
    elif given_format == "jmol":
        _show_jmol(given_format, nodes)
    elif given_format == "vesta":
        _show_vesta(given_format, nodes)
    elif given_format == "vmd":
        _show_vmd(given_format, nodes)
    elif given_format == "xcrysden":
        _show_xcrysden(given_format, nodes)
    else:
        raise NotImplementedError("The format {} is not yet implemented"
                                  .format(given_format))

project_headers = ["Id", "Label", "Kinds", "Sites"]
@structure.command('list')
@list_options
def list_structures(elements, elements_only, raw, formulamode, past_days,
                    groups, all_users):
    """
    List stored StructureData objects
    """
    from aiida.orm.data.structure import StructureData
    from aiida.orm.data.structure import (get_formula, get_symbols_string)
    from tabulate import tabulate


    lst = _list(StructureData, project_headers, elements, elements_only, formulamode, past_days, groups, all_users)

    entry_list = []
    for [id, label, akinds, asites] in lst:
        # If symbols are defined there is a filtering of the structures
        # based on the element
        # When QueryBuilder will support this (attribute)s filtering,
        # it will be pushed in the query.
        if elements is not None:
            all_symbols = [_["symbols"][0] for _ in akinds]
            if not any([s in elements for s in all_symbols]):
                continue

            if elements_only:
                echo.echo_critical("Not implemented elements-only search")

        # We want only the StructureData that have attributes
        if akinds is None or asites is None:
            continue

        symbol_dict = {}
        for k in akinds:
            symbols = k['symbols']
            weights = k['weights']
            symbol_dict[k['name']] = get_symbols_string(symbols,
                                                        weights)

        try:
            symbol_list = []
            for s in asites:
                symbol_list.append(symbol_dict[s['kind_name']])
            formula = get_formula(symbol_list,
                                    mode=formulamode)
        # If for some reason there is no kind with the name
        # referenced by the site
        except KeyError:
            formula = "<<UNKNOWN>>"
        entry_list.append([str(id), str(formula), label])

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


supported_formats = ['cif', 'tcod', 'xsf', 'xyz']
# XYZ for alloys or systems with vacancies not implemented.
# supported_formats = ['cif', 'tcod', 'xsf']
@structure.command('export')
@click.option('-y', '--format',
              type=click.Choice(supported_formats),
              default='xyz',
              # default='cif',
              help="Type of the exported file.")
@export_options
def export(**kwargs):
    """
    Export structure
    """
    from aiida.orm.data.structure import StructureData

    node = kwargs.pop('node')
    output = kwargs.pop('output')
    format = kwargs.pop('format')
    force = kwargs.pop('force')

    for key,value in kwargs.items():
        if value is None:
            kwargs.pop(key)  

    if not isinstance(node, StructureData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), StructureData))
    _export(node, output, format, other_args=kwargs, overwrite=force)


@structure.command('deposit')
@deposit_options
def deposit(**kwargs):
    """
    Deposit StructureData object
    """
    from aiida.orm.data.structure import StructureData
    if not is_dbenv_loaded():
        load_dbenv()
    node = kwargs.pop('node')
    deposition_type = kwargs.pop('deposition_type')
    parameter_data = kwargs.pop('parameter_data')

    #if kwargs['database'] is None:
        #echo.echo_critical("Default database is not defined, please specify.")
    kwargs.pop('database') # looks like a bug, but deposit function called inside deposit_tcod complains about the 'database' keywords argument
    
    for key,value in kwargs.items():
        if value is None:
            kwargs.pop(key) 

    if not isinstance(node, StructureData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), StructureData))
    echo.echo(deposit_tcod(node, deposition_type, parameter_data, **kwargs))


def _import_xyz(filename, **kwargs):
    """
    Imports an XYZ-file.
    """
    from os.path import abspath
    from aiida.orm.data.structure import StructureData

    vacuum_addition = kwargs.pop('vacuum_addition')
    vacuum_factor = kwargs.pop('vacuum_factor')
    pbc = [bool(i) for i in kwargs.pop('pbc')]
    store = kwargs.pop('store')
    view_in_ase = kwargs.pop('view')

    echo.echo('importing XYZ-structure from: \n  {}'.format(abspath(filename)))
    filepath = abspath(filename)
    with open(filepath) as f:
        xyz_txt = f.read()
    new_structure = StructureData()
    try:
        new_structure._parse_xyz(xyz_txt)
        new_structure._adjust_default_cell(vacuum_addition=vacuum_addition,
                                            vacuum_factor=vacuum_factor,
                                            pbc=pbc)

        if store:
            new_structure.store()
        if view_in_ase:
            from ase.visualize import view
            view(new_structure.get_ase())
        echo.echo(
            '  Succesfully imported structure {}, '
            '(PK = {})'.format(new_structure.get_formula(), new_structure.pk)
        )

    except ValueError as e:
        echo.echo_critical(e)


def _import_pwi(filename, **kwargs):
    """
    Imports a structure from a quantumespresso input file.
    """
    from os.path import abspath
    try:
        from qe_tools.parsers.pwinputparser import PwInputFile
    except ImportError:
        echo.echo_critical ("You have not installed the package qe-tools. \n"
                "You can install it with: pip install qe-tools")

    store = kwargs.pop('store')
    view_in_ase = kwargs.pop('view')

    echo.echo('importing structure from: \n  {}'.format(abspath(filename)))
    filepath = abspath(filename)

    try:
        inputparser = PwInputFile(filepath)
        new_structure = inputparser.get_structuredata()

        if store:
            new_structure.store()
        if view_in_ase:
            from ase.visualize import view
            view(new_structure.get_ase())
        echo.echo(
            '  Succesfully imported structure {}, '
            '(PK = {})'.format(new_structure.get_formula(), new_structure.pk)
        )

    except ValueError as e:
        echo.echo_critical(e)

def _import_ase(filename, **kwargs):
    """
    Imports a structure in a number of formats using the ASE routines.
    """
    from os.path import abspath
    from aiida.orm.data.structure import StructureData

    try:
        import ase.io
    except ImportError:
        echo.echo_critical ("You have not installed the package ase. \n"
                "You can install it with: pip install ase")

    store = kwargs.pop('store')
    view_in_ase = kwargs.pop('view')

    echo.echo( 'importing structure from: \n  {}'.format(abspath(filename)))
    filepath = abspath(filename)

    try:
        asecell = ase.io.read(filepath)
        new_structure = StructureData(ase=asecell)

        if store:
            new_structure.store()
        if view_in_ase:
            from ase.visualize import view
            view(new_structure.get_ase())
        echo.echo(
            '  Succesfully imported structure {}, '
            '(PK = {})'.format(new_structure.get_formula(), new_structure.pk)
        )

    except ValueError as e:
        echo.echo_critical(e)

@structure.command('import')
@click.option('--file', 'filename',
              type=click.Path(exists=True, dir_okay=False, resolve_path=True),
              help="Path of the imported file. Reads from standard"
              " input if not specified")
@click.option('-f', '--format', 'given_format',
              type=click.Choice(['ase', 'pwi', 'xyz']),
              default='xyz',
              help="Type of the imported file.")
@click.option('--vacuum-factor', type=click.FLOAT,
              default=1.0,
              help="The factor by which the cell accomodating the"
              " structure should be increased, default: 1.0")
@click.option('--vacuum-addition', type=click.FLOAT,
              default=10.0,
              help="The distance to add to the unit cell after"
              " vacuum factor was applied to expand in each"
              " dimension, default: 10.0")
@click.option('--pbc', type=click.INT,
              nargs=3,
              default=[0, 0, 0],
              help="Set periodic boundary conditions for each"
              " lattice direction, 0 for no periodicity, any"
              " other integer for periodicity")
@click.option('--view', is_flag=True,
              default=False,
              help='View resulting structure using ASE.')
@click.option('--dont-store', 'store', is_flag=True,
              default=True,
              help='Do not store the structure in AiiDA database.')
def structure_import(filename, given_format, vacuum_factor, vacuum_addition,
                     pbc, view, store):
    """
    Import structure
    """
    if not is_dbenv_loaded():
        load_dbenv()
    if not filename:
        filename = "/dev/stdin"
    
    args = {}
    if vacuum_factor is not None:
        args['vacuum_factor'] = vacuum_factor
    if vacuum_addition is not None:
        args['vacuum_addition'] = vacuum_addition
    if pbc is not None:
        args['pbc'] = pbc
    if view is not None:
        args['view'] = view
    if store is not None:
        args['store'] = store

    if given_format == "ase":
        _import_ase(filename, **args)
    elif given_format == "pwi":
        _import_pwi(filename, **args)
    elif given_format == "xyz":
        _import_xyz(filename, **args)
    else:
        raise NotImplementedError("The format {} is not yet implemented"
                                  .format(given_format))
