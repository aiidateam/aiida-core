# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-arguments,import-error,too-many-locals,unused-argument
"""`verdi export` command."""
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators
from aiida.common.links import GraphTraversalRules

from aiida.cmdline.commands import cmd_archive


@verdi.group('export', hidden=True)
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi archive' instead.")
def verdi_export():
    """Deprecated, use `verdi archive`."""


@verdi_export.command('inspect')
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi archive inspect' instead.")
@click.argument('archive', nargs=1, type=click.Path(exists=True, readable=True))
@click.option('-v', '--version', is_flag=True, help='Print the archive format version and exit.')
@click.option('-d', '--data', hidden=True, is_flag=True, help='Print the data contents and exit.')
@click.option('-m', '--meta-data', is_flag=True, help='Print the meta data contents and exit.')
@click.pass_context
def inspect(ctx, archive, version, data, meta_data):
    """Inspect contents of an exported archive without importing it.

    By default a summary of the archive contents will be printed. The various options can be used to change exactly what
    information is displayed.

    .. deprecated:: 1.5.0
        Support for the --data flag

    """
    ctx.forward(cmd_archive.inspect)


@verdi_export.command('create')
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi archive create' instead.")
@arguments.OUTPUT_FILE(type=click.Path(exists=False))
@options.CODES()
@options.COMPUTERS()
@options.GROUPS()
@options.NODES()
@options.ARCHIVE_FORMAT(
    type=click.Choice(['zip', 'zip-uncompressed', 'zip-lowmemory', 'tar.gz', 'null']),
)
@options.FORCE(help='overwrite output file if it already exists')
@click.option(
    '-v',
    '--verbosity',
    default='INFO',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'CRITICAL']),
    help='Control the verbosity of console logging'
)
@options.graph_traversal_rules(GraphTraversalRules.EXPORT.value)
@click.option(
    '--include-logs/--exclude-logs',
    default=True,
    show_default=True,
    help='Include or exclude logs for node(s) in export.'
)
@click.option(
    '--include-comments/--exclude-comments',
    default=True,
    show_default=True,
    help='Include or exclude comments for node(s) in export. (Will also export extra users who commented).'
)
@click.pass_context
@decorators.with_dbenv()
def create(
    ctx, output_file, codes, computers, groups, nodes, archive_format, force, input_calc_forward, input_work_forward,
    create_backward, return_backward, call_calc_backward, call_work_backward, include_comments, include_logs, verbosity
):
    """
    Export subsets of the provenance graph to file for sharing.

    Besides Nodes of the provenance graph, you can export Groups, Codes, Computers, Comments and Logs.

    By default, the archive file will include not only the entities explicitly provided via the command line but also
    their provenance, according to the rules outlined in the documentation.
    You can modify some of those rules using options of this command.
    """
    ctx.forward(cmd_archive.create)


@verdi_export.command('migrate')
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi archive migrate' instead.")
@arguments.INPUT_FILE()
@arguments.OUTPUT_FILE(required=False)
@options.ARCHIVE_FORMAT()
@options.FORCE(help='overwrite output file if it already exists')
@click.option('-i', '--in-place', is_flag=True, help='Migrate the archive in place, overwriting the original file.')
@options.SILENT(hidden=True)
@click.option(
    '-v',
    '--version',
    type=click.STRING,
    required=False,
    metavar='VERSION',
    # Note: Adding aiida.tools.EXPORT_VERSION as a default value explicitly would result in a slow import of
    # aiida.tools and, as a consequence, aiida.orm. As long as this is the case, better determine the latest export
    # version inside the function when needed.
    help='Archive format version to migrate to (defaults to latest version).',
)
@click.option(
    '--verbosity',
    default='INFO',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'CRITICAL']),
    help='Control the verbosity of console logging'
)
@click.pass_context
def migrate(ctx, input_file, output_file, force, silent, in_place, archive_format, version, verbosity):
    """Migrate an export archive to a more recent format version.

    .. deprecated:: 1.5.0
        Support for the --silent flag, replaced by --verbosity

    """
    ctx.forward(cmd_archive.migrate)
