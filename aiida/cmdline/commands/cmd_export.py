# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-arguments,import-error,too-many-locals
"""`verdi export` command."""
import click
import tabulate

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options
from aiida.cmdline.utils import decorators
from aiida.cmdline.utils import echo
from aiida.common.links import GraphTraversalRules


@verdi.group('export')
def verdi_export():
    """Create and manage export archives."""


@verdi_export.command('inspect')
@click.argument('archive', nargs=1, type=click.Path(exists=True, readable=True))
@click.option('-v', '--version', is_flag=True, help='Print the archive format version and exit.')
@click.option('-d', '--data', is_flag=True, help='Print the data contents and exit.')
@click.option('-m', '--meta-data', is_flag=True, help='Print the meta data contents and exit.')
def inspect(archive, version, data, meta_data):
    """Inspect contents of an exported archive without importing it.

    By default a summary of the archive contents will be printed. The various options can be used to change exactly what
    information is displayed.

    .. deprecated:: 1.5.0
        Support for the --data flag

    """
    import dataclasses
    from aiida.tools.importexport import CorruptArchive, detect_archive_type, get_reader

    reader_cls = get_reader(detect_archive_type(archive))

    with reader_cls(archive) as reader:
        try:
            if version:
                echo.echo(reader.export_version)
            elif data:
                # data is an internal implementation detail
                echo.echo_deprecated('--data is deprecated and will be removed in v2.0.0')
                echo.echo_dictionary(reader._get_data())  # pylint: disable=protected-access
            elif meta_data:
                echo.echo_dictionary(dataclasses.asdict(reader.metadata))
            else:
                statistics = {
                    'Version aiida': reader.metadata.aiida_version,
                    'Version format': reader.metadata.export_version,
                    'Computers': reader.entity_count('Computer'),
                    'Groups': reader.entity_count('Group'),
                    'Links': reader.link_count,
                    'Nodes': reader.entity_count('Node'),
                    'Users': reader.entity_count('User'),
                }
                if reader.metadata.conversion_info:
                    statistics['Conversion info'] = '\n'.join(reader.metadata.conversion_info)

                echo.echo(tabulate.tabulate(statistics.items()))
        except CorruptArchive as exception:
            echo.echo_critical(f'corrupt archive: {exception}')


@verdi_export.command('create')
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
# will only be useful when moving to a new archive format, that does not store all data in memory
# @click.option(
#     '-b',
#     '--batch-size',
#     default=1000,
#     type=int,
#     help='Batch database query results in sub-collections to reduce memory usage.'
# )
@decorators.with_dbenv()
def create(
    output_file, codes, computers, groups, nodes, archive_format, force, input_calc_forward, input_work_forward,
    create_backward, return_backward, call_calc_backward, call_work_backward, include_comments, include_logs, verbosity
):
    """
    Export subsets of the provenance graph to file for sharing.

    Besides Nodes of the provenance graph, you can export Groups, Codes, Computers, Comments and Logs.

    By default, the archive file will include not only the entities explicitly provided via the command line but also
    their provenance, according to the rules outlined in the documentation.
    You can modify some of those rules using options of this command.
    """
    # pylint: disable=too-many-branches
    from aiida.common.log import override_log_formatter_context
    from aiida.common.progress_reporter import set_progress_bar_tqdm, set_progress_reporter
    from aiida.tools.importexport import export, ExportFileFormat, EXPORT_LOGGER
    from aiida.tools.importexport.common.exceptions import ArchiveExportError

    entities = []

    if codes:
        entities.extend(codes)

    if computers:
        entities.extend(computers)

    if groups:
        entities.extend(groups)

    if nodes:
        entities.extend(nodes)

    kwargs = {
        'input_calc_forward': input_calc_forward,
        'input_work_forward': input_work_forward,
        'create_backward': create_backward,
        'return_backward': return_backward,
        'call_calc_backward': call_calc_backward,
        'call_work_backward': call_work_backward,
        'include_comments': include_comments,
        'include_logs': include_logs,
        'overwrite': force,
    }

    if archive_format == 'zip':
        export_format = ExportFileFormat.ZIP
        kwargs.update({'writer_init': {'use_compression': True}})
    elif archive_format == 'zip-uncompressed':
        export_format = ExportFileFormat.ZIP
        kwargs.update({'writer_init': {'use_compression': False}})
    elif archive_format == 'zip-lowmemory':
        export_format = ExportFileFormat.ZIP
        kwargs.update({'writer_init': {'cache_zipinfo': True}})
    elif archive_format == 'tar.gz':
        export_format = ExportFileFormat.TAR_GZIPPED
    elif archive_format == 'null':
        export_format = 'null'

    if verbosity in ['DEBUG', 'INFO']:
        set_progress_bar_tqdm(leave=(verbosity == 'DEBUG'))
    else:
        set_progress_reporter(None)
    EXPORT_LOGGER.setLevel(verbosity)

    try:
        with override_log_formatter_context('%(message)s'):
            export(entities, filename=output_file, file_format=export_format, **kwargs)
    except ArchiveExportError as exception:
        echo.echo_critical(f'failed to write the archive file. Exception: {exception}')
    else:
        echo.echo_success(f'wrote the export archive file to {output_file}')


@verdi_export.command('migrate')
@arguments.INPUT_FILE()
@arguments.OUTPUT_FILE(required=False)
@options.ARCHIVE_FORMAT()
@options.FORCE(help='overwrite output file if it already exists')
@click.option('-i', '--in-place', is_flag=True, help='Migrate the archive in place, overwriting the original file.')
@options.SILENT()
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
def migrate(input_file, output_file, force, silent, in_place, archive_format, version, verbosity):
    """Migrate an export archive to a more recent format version.

    .. deprecated:: 1.5.0
        Support for the --silent flag, replaced by --verbosity

    """
    from aiida.common.log import override_log_formatter_context
    from aiida.common.progress_reporter import set_progress_bar_tqdm, set_progress_reporter
    from aiida.tools.importexport import detect_archive_type, EXPORT_VERSION
    from aiida.tools.importexport.archive.migrators import get_migrator, MIGRATE_LOGGER

    if silent is True:
        echo.echo_deprecated('the --silent option is deprecated, use --verbosity')

    if in_place:
        if output_file:
            echo.echo_critical('output file specified together with --in-place flag')
        output_file = input_file
        force = True
    elif not output_file:
        echo.echo_critical(
            'no output file specified. Please add --in-place flag if you would like to migrate in place.'
        )

    if verbosity in ['DEBUG', 'INFO']:
        set_progress_bar_tqdm(leave=(verbosity == 'DEBUG'))
    else:
        set_progress_reporter(None)
    MIGRATE_LOGGER.setLevel(verbosity)

    if version is None:
        version = EXPORT_VERSION

    migrator_cls = get_migrator(detect_archive_type(input_file))
    migrator = migrator_cls(input_file)

    try:
        with override_log_formatter_context('%(message)s'):
            migrator.migrate(version, output_file, force=force, out_compression=archive_format)
    except Exception as error:  # pylint: disable=broad-except
        if verbosity == 'DEBUG':
            raise
        echo.echo_critical(
            'failed to migrate the archive file (use `--verbosity DEBUG` to see traceback): '
            f'{error.__class__.__name__}:{error}'
        )

    if verbosity in ['DEBUG', 'INFO']:
        echo.echo_success(f'migrated the archive to version {version}')
