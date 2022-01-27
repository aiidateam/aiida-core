# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data structure` command."""

import click

from aiida.cmdline.commands.cmd_data import cmd_show, verdi_data
from aiida.cmdline.commands.cmd_data.cmd_export import data_export, export_options
from aiida.cmdline.commands.cmd_data.cmd_list import data_list, list_options
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo
from aiida.cmdline.utils.pluginable import Pluginable

LIST_PROJECT_HEADERS = ['Id', 'Label', 'Formula']
EXPORT_FORMATS = ['cif', 'xsf', 'xyz']
VISUALIZATION_FORMATS = ['ase', 'jmol', 'vesta', 'vmd', 'xcrysden']


def _store_structure(new_structure, dry_run):
    """
    Store a structure and print a message (or don't store it if it's a dry_run)

    This is a utility function to avoid code duplication.

    :param new_structure: an unstored StructureData
    :param dry_run: if True, do not store but print a different message
    """
    if dry_run:
        echo.echo(
            f'  Successfully imported structure {new_structure.get_formula()} (not storing it, dry-run requested)'
        )
    else:
        new_structure.store()
        echo.echo(f'  Successfully imported structure {new_structure.get_formula()} (PK = {new_structure.pk})')


@verdi_data.group('structure')
def structure():
    """Manipulate StructureData objects (crystal structures)."""


# pylint: disable=too-many-locals,too-many-branches
@structure.command('list')
@options.FORMULA_MODE()
@options.WITH_ELEMENTS()
@list_options
@decorators.with_dbenv()
def structure_list(elements, raw, formula_mode, past_days, groups, all_users):
    """List StructureData objects."""
    from tabulate import tabulate

    from aiida.orm.nodes.data.structure import StructureData, get_formula, get_symbols_string

    elements_only = False
    lst = data_list(
        StructureData, ['Id', 'Label', 'Kinds', 'Sites'], elements, elements_only, formula_mode, past_days, groups,
        all_users
    )

    entry_list = []
    for [pid, label, akinds, asites] in lst:
        # If symbols are defined there is a filtering of the structures
        # based on the element
        # When QueryBuilder will support this (attribute)s filtering,
        # it will be pushed in the query.
        if elements is not None:
            all_symbols = [_['symbols'][0] for _ in akinds]
            if not any(s in elements for s in all_symbols):
                continue

            if elements_only:
                echo.echo_critical('Not implemented elements-only search')

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
            formula = '<<UNKNOWN>>'
        entry_list.append([str(pid), label, str(formula)])

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


@structure.command('show')
@arguments.DATA(type=types.DataParamType(sub_classes=('aiida.data:core.structure',)))
@options.VISUALIZATION_FORMAT(type=click.Choice(VISUALIZATION_FORMATS), default='ase')
@decorators.with_dbenv()
def structure_show(data, fmt):
    """Visualize StructureData objects."""
    try:
        show_function = getattr(cmd_show, f'_show_{fmt}')
    except AttributeError:
        echo.echo_critical(f'visualization format {fmt} is not supported')

    show_function(fmt, data)


@structure.command('export')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:core.structure',)))
@options.EXPORT_FORMAT(
    type=click.Choice(EXPORT_FORMATS),
    default='xyz',
)
@export_options
@decorators.with_dbenv()
def structure_export(**kwargs):
    """Export StructureData object to file."""
    node = kwargs.pop('datum')
    output = kwargs.pop('output')
    fmt = kwargs.pop('fmt')
    force = kwargs.pop('force')

    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    data_export(node, output, fmt, other_args=kwargs, overwrite=force)


@structure.group('import', entry_point_group='aiida.cmdline.data.structure.import', cls=Pluginable)
def structure_import():
    """Import a crystal structure from file into a StructureData object."""


@structure_import.command('aiida-xyz')
@click.argument('filename', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option(
    '--vacuum-factor',
    type=click.FLOAT,
    show_default=True,
    default=1.0,
    help='The factor by which the cell accomodating the structure should be increased (angstrom).'
)
@click.option(
    '--vacuum-addition',
    type=click.FLOAT,
    show_default=True,
    default=10.0,
    help='The distance to add to the unit cell after vacuum factor was applied to expand in each dimension (angstrom).'
)
@click.option(
    '--pbc',
    type=click.INT,
    nargs=3,
    show_default=True,
    default=[0, 0, 0],
    help='Set periodic boundary conditions for each lattice direction, where 0 means periodic and 1 means periodic.'
)
@click.option('--label', type=click.STRING, show_default=False, help='Set the structure node label (empty by default)')
@options.GROUP()
@options.DRY_RUN()
@decorators.with_dbenv()
def import_aiida_xyz(filename, vacuum_factor, vacuum_addition, pbc, label, group, dry_run):
    """
    Import structure in XYZ format using AiiDA's internal importer
    """
    from aiida.orm import StructureData

    with open(filename, encoding='utf8') as fobj:
        xyz_txt = fobj.read()
    new_structure = StructureData()

    pbc_bools = []
    for pbc_int in pbc:
        if pbc_int == 0:
            pbc_bools.append(False)
        elif pbc_int == 1:
            pbc_bools.append(True)
        else:
            raise click.BadParameter('values for pbc must be either 0 or 1', param_hint='pbc')

    try:
        new_structure._parse_xyz(xyz_txt)  # pylint: disable=protected-access
        new_structure._adjust_default_cell(  # pylint: disable=protected-access
            vacuum_addition=vacuum_addition,
            vacuum_factor=vacuum_factor,
            pbc=pbc_bools)

    except (ValueError, TypeError) as err:
        echo.echo_critical(str(err))

    if label:
        new_structure.label = label

    _store_structure(new_structure, dry_run)

    if group:
        group.add_nodes(new_structure)


@structure_import.command('ase')
@click.argument('filename', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--label', type=click.STRING, show_default=False, help='Set the structure node label (empty by default)')
@options.GROUP()
@options.DRY_RUN()
@decorators.with_dbenv()
def import_ase(filename, label, group, dry_run):
    """
    Import structure with the ase library that supports a number of different formats
    """
    from aiida.orm import StructureData

    try:
        import ase.io
    except ImportError:
        echo.echo_critical('You have not installed the package ase. \nYou can install it with: pip install ase')

    try:
        asecell = ase.io.read(filename)
        new_structure = StructureData(ase=asecell)
    except ValueError as err:
        echo.echo_critical(str(err))

    if label:
        new_structure.label = label

    _store_structure(new_structure, dry_run)

    if group:
        group.add_nodes(new_structure)
