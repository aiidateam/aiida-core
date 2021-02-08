# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi import` command."""
# pylint: disable=broad-except,unused-argument
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.params.types import GroupParamType, PathOrUrl
from aiida.cmdline.utils import decorators

from aiida.cmdline.commands.cmd_archive import import_archive, EXTRAS_MODE_EXISTING, EXTRAS_MODE_NEW, COMMENT_MODE


@verdi.command('import', hidden=True)
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi archive import' instead.")
@click.argument('archives', nargs=-1, type=PathOrUrl(exists=True, readable=True))
@click.option(
    '-w',
    '--webpages',
    type=click.STRING,
    cls=options.MultipleValueOption,
    help='Discover all URL targets pointing to files with the .aiida extension for these HTTP addresses. '
    'Automatically discovered archive URLs will be downloaded and added to ARCHIVES for importing'
)
@options.GROUP(
    type=GroupParamType(create_if_not_exist=True),
    help='Specify group to which all the import nodes will be added. If such a group does not exist, it will be'
    ' created automatically.'
)
@click.option(
    '-e',
    '--extras-mode-existing',
    type=click.Choice(EXTRAS_MODE_EXISTING),
    default='keep_existing',
    help='Specify which extras from the export archive should be imported for nodes that are already contained in the '
    'database: '
    'ask: import all extras and prompt what to do for existing extras. '
    'keep_existing: import all extras and keep original value of existing extras. '
    'update_existing: import all extras and overwrite value of existing extras. '
    'mirror: import all extras and remove any existing extras that are not present in the archive. '
    'none: do not import any extras.'
)
@click.option(
    '-n',
    '--extras-mode-new',
    type=click.Choice(EXTRAS_MODE_NEW),
    default='import',
    help='Specify whether to import extras of new nodes: '
    'import: import extras. '
    'none: do not import extras.'
)
@click.option(
    '--comment-mode',
    type=click.Choice(COMMENT_MODE),
    default='newest',
    help='Specify the way to import Comments with identical UUIDs: '
    'newest: Only the newest Comments (based on mtime) (default).'
    'overwrite: Replace existing Comments with those from the import file.'
)
@click.option(
    '--migration/--no-migration',
    default=True,
    show_default=True,
    help='Force migration of archive file archives, if needed.'
)
@click.option(
    '-v',
    '--verbosity',
    default='INFO',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'CRITICAL']),
    help='Control the verbosity of console logging'
)
@options.NON_INTERACTIVE()
@decorators.with_dbenv()
@click.pass_context
def cmd_import(
    ctx, archives, webpages, group, extras_mode_existing, extras_mode_new, comment_mode, migration, non_interactive,
    verbosity
):
    """Deprecated, use `verdi archive import`."""
    ctx.forward(import_archive)
