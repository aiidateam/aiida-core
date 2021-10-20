# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module provides export functionality to all data types
"""

import click

from aiida.cmdline.params import options
from aiida.cmdline.utils import echo

EXPORT_OPTIONS = [
    click.option(
        '--reduce-symmetry/--no-reduce-symmetry',
        'reduce_symmetry',
        is_flag=True,
        default=None,
        help='Do (default) or do not perform symmetry reduction.'
    ),
    click.option(
        '--parameter-data',
        type=click.INT,
        default=None,
        help='ID of the Dict to be exported alongside the'
        ' StructureData instance. By default, if StructureData'
        ' originates from a calculation with single'
        ' Dict in the output, aforementioned'
        ' Dict is picked automatically. Instead, the'
        ' option is used in the case the calculation produces'
        ' more than a single instance of Dict.'
    ),
    click.option(
        '--dump-aiida-database/--no-dump-aiida-database',
        'dump_aiida_database',
        is_flag=True,
        default=None,
        help='Export (default) or do not export AiiDA database to the CIF file.'
    ),
    click.option(
        '--exclude-external-contents/--no-exclude-external-contents',
        'exclude_external_contents',
        is_flag=True,
        default=None,
        help='Do not (default) or do save the contents for external resources even if URIs are provided'
    ),
    click.option('--gzip/--no-gzip', is_flag=True, default=None, help='Do or do not (default) gzip large files.'),
    click.option(
        '--gzip-threshold',
        type=click.INT,
        default=None,
        help='Specify the minimum size of exported file which should'
        ' be gzipped.'
    ),
    click.option(
        '-o',
        '--output',
        type=click.STRING,
        default=None,
        help='If present, store the output directly on a file '
        'with the given name. It is essential to use this option '
        'if more than one file needs to be created.'
    ),
    options.FORCE(help='Overwrite files without checking.'),
]


def export_options(func):
    for option in reversed(EXPORT_OPTIONS):
        func = option(func)

    return func


def data_export(node, output_fname, fileformat, other_args=None, overwrite=False):
    """
    Depending on the parameters, either print the (single) output file on
    screen, or store the file(s) on disk.

    :param node: the Data node to print or store on disk
    :param output_fname: The filename to store the main file. If empty or
        None, print instead
    :param fileformat: a string to pass to the _exportcontent method
    :param other_args: a dictionary with additional kwargs to pass to _exportcontent
    :param overwrite: if False, stops if any file already exists (when output_fname
        is not empty

    :note: this function calls directly sys.exit(1) when an error occurs (or e.g. if
        check_overwrite is True and a file already exists).
    """
    if other_args is None:
        other_args = {}
    try:
        # pylint: disable=protected-access
        if output_fname:
            try:
                node.export(output_fname, fileformat=fileformat, overwrite=overwrite, **other_args)
            except OSError as err:
                echo.echo_critical(f'OSError while exporting file:\n{err}')
        else:
            filetext, extra_files = node._exportcontent(fileformat, main_file_name=output_fname, **other_args)
            if extra_files:
                echo.echo_critical(
                    'This format requires to write more than one file.\n'
                    'You need to pass the -o option to specify a file name.'
                )
            else:
                echo.echo(filetext.decode('utf-8'))
    except TypeError as err:
        # This typically occurs for parameters that are passed down to the
        # methods in, e.g., BandsData, but they are not accepted
        echo.echo_critical(
            f'TypeError, perhaps a parameter is not supported by the specific format?\nError message: {err}'
        )
