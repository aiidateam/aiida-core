# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This allows to manage BandsData objects from command line.
"""
from __future__ import print_function
import sys
import click
from aiida.cmdline.commands.data.list import list_options
from aiida.cmdline.commands.data.export import _export
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.commands import verdi_data
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options
from aiida.cmdline.utils import decorators, echo
from aiida.common.utils import Prettifier


def show_xmgrace(exec_name, list_bands):
    """
    Plugin for showing the bands with the XMGrace plotting software.
    """
    import tempfile
    import subprocess
    import numpy
    from aiida.orm.data.array.bands import max_num_agr_colors

    list_files = []
    current_band_number = 0
    for iband, bnds in enumerate(list_bands):
        # extract number of bands
        nbnds = bnds.get_bands().shape[1]
        # pylint: disable=protected-access
        text, _ = bnds._exportstring(
            'agr', setnumber_offset=current_band_number, color_number=numpy.mod(iband + 1, max_num_agr_colors))
        # write a tempfile
        tempf = tempfile.NamedTemporaryFile(suffix='.agr')
        tempf.write(text)
        tempf.flush()
        list_files.append(tempf)
        # update the number of bands already plotted
        current_band_number += nbnds

    try:
        subprocess.check_output([exec_name] + [f.name for f in list_files])
        _ = [f.close() for f in list_files]
    except subprocess.CalledProcessError:
        print("Note: the call to {} ended with an error.".format(exec_name))
        _ = [f.close() for f in list_files]
    except OSError as err:
        _ = [f.close() for f in list_files]
        if err.errno == 2:
            print("No executable '{}' found. Add to the path," " or try with an absolute path.".format(exec_name))
            sys.exit(1)
        else:
            raise


# pylint: disable=unused-argument
@verdi_data.group('bands')
@click.pass_context
def bands(ctx):
    """
    Manipulate BandsData objects
    """
    pass


@bands.command('show')
@decorators.with_dbenv()
@arguments.NODES()
@click.option(
    '-f',
    '--format',
    'show_format',
    type=click.Choice(['xmgrace']),
    default='xmgrace',
    help="Filter the families only to those containing "
    "a pseudo for each of the specified elements")
def show(nodes, show_format):
    """
    Visualize bands objects
    """
    from aiida.orm.data.array.bands import BandsData
    for node in nodes:
        if not isinstance(node, BandsData):
            echo.echo_critical("Node {} is of class {} instead " "of {}".format(node, type(node), BandsData))
        show_xmgrace(show_format, nodes)


PROJECT_HEADERS = ['ID', 'Formula', 'Ctime', 'Label']


# pylint: disable=too-many-arguments
@bands.command('list')
@decorators.with_dbenv()
@list_options
@click.option(
    '-e',
    '--elements',
    type=click.STRING,
    cls=MultipleValueOption,
    default=None,
    help="Print only the objects that"
    " contain desired elements")
@click.option(
    '-eo',
    '--elements-only',
    type=click.STRING,
    cls=MultipleValueOption,
    default=None,
    help="Print only the objects that"
    " contain only the selected elements")
@click.option(
    '-f',
    '--formulamode',
    type=click.Choice(['hill', 'hill_compact', 'reduce', 'group', 'count', 'count_compact']),
    default='hill',
    help="Formula printing mode (if None, does not print the formula)")
def bands_list(elements, elements_only, raw, formulamode, past_days, groups, all_users):
    """
    List bands objects
    """
    # from aiida.orm.data.cif import CifData
    from aiida.backends.utils import QueryFactory
    from tabulate import tabulate
    from argparse import Namespace

    args = Namespace()
    args.element = elements
    args.element_only = elements_only
    args.formulamode = formulamode
    args.past_days = past_days
    args.group_name = None
    if groups is not None:
        args.group_pk = [group.id for group in groups]
    else:
        args.group_pk = None
    args.all_users = all_users

    query = QueryFactory()()
    entry_list = query.get_bands_and_parents_structure(args)

    counter = 0
    bands_list_data = list()
    if not raw:
        bands_list_data.append(PROJECT_HEADERS)
    for entry in entry_list:
        for i, value in enumerate(entry):
            if isinstance(value, list):
                entry[i] = ",".join(value)
        for i in range(len(entry), len(PROJECT_HEADERS)):
            entry.append(None)
        counter += 1
    bands_list_data.extend(entry_list)
    if raw:
        echo.echo(tabulate(bands_list_data, tablefmt='plain'))
    else:
        echo.echo(tabulate(bands_list_data, headers="firstrow"))
        echo.echo("\nTotal results: {}\n".format(counter))


@bands.command('export')
@decorators.with_dbenv()
@click.option(
    '-y',
    '--format',
    'used_format',
    type=click.Choice([
        'agr', 'agr_batch', 'dat_blocks', 'dat_multicolumn', 'gnuplot', 'json', 'mpl_pdf', 'mpl_png', 'mpl_singlefile',
        'mpl_withjson'
    ]),
    default='json',
    help="Type of the exported file.")
@click.option(
    '--y-min-lim',
    type=click.FLOAT,
    default=None,
    help='The minimum value for the y axis.'
    ' Default: minimum of all bands')
@click.option(
    '--y-max-lim',
    type=click.FLOAT,
    default=None,
    help='The maximum value for the y axis.'
    ' Default: maximum of all bands')
@click.option(
    '-o',
    '--output',
    type=click.STRING,
    default=None,
    help="If present, store the output directly on a file "
    "with the given name. It is essential to use this option "
    "if more than one file needs to be created.")
@options.FORCE(help="If passed, overwrite files without checking.")
@click.option(
    '--prettify-format',
    default=None,
    type=click.Choice(Prettifier.get_prettifiers()),
    help='The style of labels for the prettifier')
@arguments.NODE()
def export(used_format, y_min_lim, y_max_lim, output, force, prettify_format, node):
    """
    Export bands objects
    """
    from aiida.orm.data.array.bands import BandsData

    args = {}
    if y_min_lim is not None:
        args['y_min_lim'] = y_min_lim
    if y_max_lim is not None:
        args['y_max_lim'] = y_max_lim
    if prettify_format is not None:
        args['prettify_format'] = prettify_format

    if not isinstance(node, BandsData):
        echo.echo_critical("Node {} is of class {} instead of {}".format(node, type(node), BandsData))
    _export(node, output, used_format, other_args=args, overwrite=force)
