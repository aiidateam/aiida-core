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
This module provides deposit functionality to all data types
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click
from aiida.cmdline.params import options, types

DEPOSIT_OPTIONS = [
    options.CODE(help='Code to be used for the deposition.'),
    options.COMPUTER(help='Computer to be used for deposition.'),
    click.option(
        '-d', '--database', type=click.Choice(['tcod']), default='tcod', help='Label of the database for deposition.'),
    click.option(
        '--deposition-type',
        type=click.Choice(['published', 'prepublication', 'personal']),
        default='published',
        help='Type of the deposition.'),
    click.option('-u', '--username', type=click.STRING, default=None, help="Depositor's username."),
    click.option('-p', '--password', is_flag=True, default=False, help="Prompt for depositor's password."),
    click.option('--user-email', type=click.STRING, default=None, help="Depositor's e-mail address."),
    click.option('--title', type=click.STRING, default=None, help="Title of the publication."),
    click.option('--author-name', type=click.STRING, default=None, help="Full name of the publication author."),
    click.option('--author-email', type=click.STRING, default=None, help="E-mail address of the publication author."),
    click.option('--url', type=click.STRING, default=None, help="URL of the deposition API."),
    click.option(
        '--parameters',
        type=types.DataParamType(sub_classes=('aiida.data:dict',)),
        help="Dict to be exported alongside the to be deposited Data node. By default, if "
        "the node originates from a calculation with single Dict in the output, aforementioned "
        "Dict is picked automatically. Instead, the option is used in the case the calculation produces "
        "more than a single instance of Dict."),
    click.option(
        '--replace', type=click.INT, default=None, help="ID of the structure to be redeposited (replaced), if any."),
    click.option(
        '-m',
        '--message',
        type=click.STRING,
        default=None,
        help="Description of the change (relevant for redepositions only)."),
    click.option(
        '--reduce-symmetry/--no-reduce-symmetry',
        'reduce_symmetry',
        is_flag=True,
        default=None,
        help='Do (default) or do not perform symmetry reduction.'),
    click.option(
        '--dump-aiida-database/--no-dump-aiida-database',
        'dump_aiida_database',
        is_flag=True,
        default=None,
        help='Export (default) or do not export AiiDA database to the CIF file.'),
    click.option(
        '--exclude-external-contents/--no-exclude-external-contents',
        'exclude_external_contents',
        is_flag=True,
        default=None,
        help='Do not (default) or do save the contents for external resources even if URIs are provided'),
    click.option(
        '--gzip/--no-gzip', 'gzip', is_flag=True, default=None, help='Do or do not (default) gzip large files.'),
    click.option(
        '--gzip-threshold',
        type=click.INT,
        default=None,
        help="Specify the minimum size of exported file which should be gzipped."),
]


def deposit_options(func):
    for option in reversed(DEPOSIT_OPTIONS):
        func = option(func)

    return func


def data_deposit_tcod(node, deposit_type, parameters=None, **kwargs):
    """
    Deposition plugin for TCOD.
    """
    from aiida.tools.dbexporters.tcod import deposit
    return deposit(node, deposit_type, parameters=parameters, **kwargs)
