# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data structure` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from six.moves import range

import click

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.commands.cmd_data import cmd_show
from aiida.cmdline.commands.cmd_data.cmd_export import data_export, export_options
from aiida.cmdline.commands.cmd_data.cmd_list import data_list, list_options
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo

LIST_PROJECT_HEADERS = ['Id', 'Label', 'Kinds', 'Sites']
EXPORT_FORMATS = ['cif', 'xsf', 'xyz']
IMPORT_FORMATS = ['ase', 'pwi', 'xyz']
VISUALIZATION_FORMATS = ['ase', 'jmol', 'vesta', 'vmd', 'xcrysden']


@verdi_data.group('structure')
def structure():
    """Manipulation of StructureData objects."""


# pylint: disable=too-many-locals,too-many-branches
@structure.command('list')
@options.FORMULA_MODE()
@options.WITH_ELEMENTS()
@list_options
@decorators.with_dbenv()
def structure_list(elements, raw, formula_mode, past_days, groups, all_users):
    """List stored StructureData objects."""
    from aiida.orm.nodes.data.structure import StructureData, get_formula, get_symbols_string
    from tabulate import tabulate

    elements_only = False
    lst = data_list(StructureData, LIST_PROJECT_HEADERS, elements, elements_only, formula_mode, past_days, groups,
                    all_users)

    entry_list = []
    for [pid, label, akinds, asites] in lst:
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
            symbol_dict[k['name']] = get_symbols_string(symbols, weights)

        try:
            symbol_list = []
            for site in asites:
                symbol_list.append(symbol_dict[site['kind_name']])
            formula = get_formula(symbol_list, mode=formula_mode)
        # If for some reason there is no kind with the name
        # referenced by the site
        except KeyError:
            formula = "<<UNKNOWN>>"
        entry_list.append([str(pid), str(formula), label])

    counter = 0
    struct_list_data = list()
    if not raw:
        struct_list_data.append(LIST_PROJECT_HEADERS)
    for entry in entry_list:
        for i, value in enumerate(entry):
            if isinstance(value, list):
                entry[i] = ",".join(value)
        for i in range(len(entry), len(LIST_PROJECT_HEADERS)):
            entry.append(None)
        counter += 1
    struct_list_data.extend(entry_list)
    if raw:
        echo.echo(tabulate(struct_list_data, tablefmt='plain'))
    else:
        echo.echo(tabulate(struct_list_data, headers="firstrow"))
        echo.echo("\nTotal results: {}\n".format(counter))


@structure.command('show')
@arguments.DATA(type=types.DataParamType(sub_classes=('aiida.data:structure',)))
@options.VISUALIZATION_FORMAT(type=click.Choice(VISUALIZATION_FORMATS), default='ase')
@decorators.with_dbenv()
def structure_show(data, fmt):
    """Visualize StructureData objects."""
    try:
        show_function = getattr(cmd_show, '_show_{}'.format(fmt))
    except AttributeError:
        echo.echo_critical('visualization format {} is not supported'.format(fmt))

    show_function(fmt, data)


@structure.command('export')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:structure',)))
@options.EXPORT_FORMAT(
    type=click.Choice(EXPORT_FORMATS),
    default='xyz',
)
@export_options
@decorators.with_dbenv()
def structure_export(**kwargs):
    """Export StructureData object."""
    node = kwargs.pop('datum')
    output = kwargs.pop('output')
    fmt = kwargs.pop('fmt')
    force = kwargs.pop('force')

    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    data_export(node, output, fmt, other_args=kwargs, overwrite=force)


# pylint: disable=too-many-arguments
@structure.command('import')
@click.argument('filename', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@options.INPUT_FORMAT(type=click.Choice(IMPORT_FORMATS))
@click.option(
    '--vacuum-factor',
    type=click.FLOAT,
    show_default=True,
    default=1.0,
    help="The factor by which the cell accomodating the structure should be increased.")
@click.option(
    '--vacuum-addition',
    type=click.FLOAT,
    show_default=True,
    default=10.0,
    help='The distance to add to the unit cell after vacuum factor was applied to expand in each dimension')
@click.option(
    '--pbc',
    type=click.INT,
    nargs=3,
    show_default=True,
    default=[0, 0, 0],
    help='Set periodic boundary conditions for each lattice direction, where 0 means no periodicity')
@click.option('--view', is_flag=True, default=False, help='View resulting structure using ASE.')
@click.option('--store', is_flag=True, default=False, help='Do not store the structure in AiiDA database.')
@decorators.with_dbenv()
def structure_import(filename, fmt, vacuum_factor, vacuum_addition, pbc, view, store):
    """
    Import structure
    """
    from aiida.cmdline.commands.cmd_data import cmd_import

    args = {
        'vacuum_factor': vacuum_factor,
        'vacuum_addition': vacuum_addition,
        'pbc': pbc,
        'view': view,
        'store': store,
    }

    try:
        show_function = getattr(cmd_import, 'data_import_{}'.format(fmt))
    except AttributeError:
        echo.echo_critical('import format {} is not supported'.format(fmt))

    show_function(filename, **args)
