# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data bands` command."""

import click

from aiida.cmdline.commands.cmd_data import cmd_show, verdi_data
from aiida.cmdline.commands.cmd_data.cmd_export import data_export
from aiida.cmdline.commands.cmd_data.cmd_list import list_options
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo
from aiida.common.utils import Prettifier

LIST_PROJECT_HEADERS = ['ID', 'Formula', 'Ctime', 'Label']
EXPORT_FORMATS = [
    'agr', 'agr_batch', 'dat_blocks', 'dat_multicolumn', 'gnuplot', 'json', 'mpl_pdf', 'mpl_png', 'mpl_singlefile',
    'mpl_withjson'
]
VISUALIZATION_FORMATS = ['xmgrace']


@verdi_data.group('bands')
def bands():
    """Manipulate BandsData objects (band structures)."""


# pylint: disable=too-many-arguments
@bands.command('list')
@decorators.with_dbenv()
@list_options
@options.WITH_ELEMENTS()
@options.WITH_ELEMENTS_EXCLUSIVE()
@options.FORMULA_MODE()
def bands_list(elements, elements_exclusive, raw, formula_mode, past_days, groups, all_users):
    """List BandsData objects."""
    from argparse import Namespace

    from tabulate import tabulate

    from aiida.orm.nodes.data.array.bands import get_bands_and_parents_structure

    args = Namespace()
    args.element = elements
    args.element_only = elements_exclusive
    args.formulamode = formula_mode
    args.past_days = past_days
    args.group_name = None
    if groups is not None:
        args.group_pk = [group.pk for group in groups]
    else:
        args.group_pk = None
    args.all_users = all_users

    entry_list = get_bands_and_parents_structure(args)

    counter = 0
    bands_list_data = []
    if not raw:
        bands_list_data.append(LIST_PROJECT_HEADERS)
    for entry in entry_list:
        for i, value in enumerate(entry):
            if isinstance(value, list):
                entry[i] = ','.join(value)
        for i in range(len(entry), len(LIST_PROJECT_HEADERS)):
            entry.append(None)
        counter += 1
    bands_list_data.extend(entry_list)
    if raw:
        echo.echo(tabulate(bands_list_data, tablefmt='plain'))
    else:
        echo.echo(tabulate(bands_list_data, headers='firstrow'))
        echo.echo(f'\nTotal results: {counter}\n')


@bands.command('show')
@arguments.DATA(type=types.DataParamType(sub_classes=('aiida.data:core.array.bands',)))
@options.VISUALIZATION_FORMAT(type=click.Choice(VISUALIZATION_FORMATS), default='xmgrace')
@decorators.with_dbenv()
def bands_show(data, fmt):
    """Visualize BandsData objects."""
    try:
        show_function = getattr(cmd_show, f'_show_{fmt}')
    except AttributeError:
        echo.echo_critical(f'visualization format {fmt} is not supported')

    show_function(fmt, data)


@bands.command('export')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:core.array.bands',)))
@options.EXPORT_FORMAT(type=click.Choice(EXPORT_FORMATS), default='json')
@click.option(
    '--y-min-lim',
    type=click.FLOAT,
    default=None,
    help='The minimum value for the y axis.'
    ' Default: minimum of all bands'
)
@click.option(
    '--y-max-lim',
    type=click.FLOAT,
    default=None,
    help='The maximum value for the y axis.'
    ' Default: maximum of all bands'
)
@click.option(
    '-o',
    '--output',
    type=click.STRING,
    default=None,
    help='If present, store the output directly on a file '
    'with the given name. It is essential to use this option '
    'if more than one file needs to be created.'
)
@options.FORCE(help='If passed, overwrite files without checking.')
@click.option(
    '--prettify-format',
    default=None,
    type=click.Choice(Prettifier.get_prettifiers()),
    help='The style of labels for the prettifier'
)
@decorators.with_dbenv()
def bands_export(fmt, y_min_lim, y_max_lim, output, force, prettify_format, datum):
    """Export BandsData objects."""
    args = {}
    if y_min_lim is not None:
        args['y_min_lim'] = y_min_lim
    if y_max_lim is not None:
        args['y_max_lim'] = y_max_lim
    if prettify_format is not None:
        args['prettify_format'] = prettify_format

    data_export(datum, output, fmt, other_args=args, overwrite=force)
