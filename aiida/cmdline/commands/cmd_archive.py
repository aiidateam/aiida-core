# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-arguments,import-error,too-many-locals,broad-except
"""`verdi archive` command."""
from enum import Enum
from typing import List, Tuple
import traceback
import urllib.request

import click
import tabulate

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.params.types import GroupParamType, PathOrUrl
from aiida.cmdline.utils import decorators, echo
from aiida.common.links import GraphTraversalRules

EXTRAS_MODE_EXISTING = ['keep_existing', 'update_existing', 'mirror', 'none', 'ask']
EXTRAS_MODE_NEW = ['import', 'none']
COMMENT_MODE = ['newest', 'overwrite']


@verdi.group('archive')
def verdi_archive():
    """Create, inspect and import AiiDA archives."""


@verdi_archive.command('inspect')
@click.argument('archive', nargs=1, type=click.Path(exists=True, readable=True))
@click.option('-v', '--version', is_flag=True, help='Print the archive format version and exit.')
@click.option('-d', '--data', hidden=True, is_flag=True, help='Print the data contents and exit.')
@click.option('-m', '--meta-data', is_flag=True, help='Print the meta data contents and exit.')
def inspect(archive, version, data, meta_data):
    """Inspect contents of an archive without importing it.

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


@verdi_archive.command('create')
@arguments.OUTPUT_FILE(type=click.Path(exists=False))
@options.CODES()
@options.COMPUTERS()
@options.GROUPS()
@options.NODES()
@options.ARCHIVE_FORMAT(
    type=click.Choice(['zip', 'zip-uncompressed', 'zip-lowmemory', 'tar.gz', 'null']),
)
@options.FORCE(help='Overwrite output file if it already exists.')
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


@verdi_archive.command('migrate')
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


class ExtrasImportCode(Enum):
    """Exit codes for the verdi command line."""
    keep_existing = 'kcl'
    update_existing = 'kcu'
    mirror = 'ncu'
    none = 'knl'
    ask = 'kca'


@verdi_archive.command('import')
@click.argument('archives', nargs=-1, type=PathOrUrl(exists=True, readable=True))
@click.option(
    '-w',
    '--webpages',
    type=click.STRING,
    cls=options.MultipleValueOption,
    help='Discover all URL targets pointing to files with the .aiida extension for these HTTP addresses. '
    'Automatically discovered archive URLs will be downloaded and added to ARCHIVES for importing.'
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
def import_archive(
    ctx, archives, webpages, group, extras_mode_existing, extras_mode_new, comment_mode, migration, non_interactive,
    verbosity
):
    """Import data from an AiiDA archive file.

    The archive can be specified by its relative or absolute file path, or its HTTP URL.
    """
    # pylint: disable=unused-argument
    from aiida.common.log import override_log_formatter_context
    from aiida.common.progress_reporter import set_progress_bar_tqdm, set_progress_reporter
    from aiida.tools.importexport.dbimport.utils import IMPORT_LOGGER
    from aiida.tools.importexport.archive.migrators import MIGRATE_LOGGER

    if verbosity in ['DEBUG', 'INFO']:
        set_progress_bar_tqdm(leave=(verbosity == 'DEBUG'))
    else:
        set_progress_reporter(None)
    IMPORT_LOGGER.setLevel(verbosity)
    MIGRATE_LOGGER.setLevel(verbosity)

    all_archives = _gather_imports(archives, webpages)

    # Preliminary sanity check
    if not all_archives:
        echo.echo_critical('no valid exported archives were found')

    # Shared import key-word arguments
    import_kwargs = {
        'group': group,
        'extras_mode_existing': ExtrasImportCode[extras_mode_existing].value,
        'extras_mode_new': extras_mode_new,
        'comment_mode': comment_mode,
    }

    with override_log_formatter_context('%(message)s'):
        for archive, web_based in all_archives:
            _import_archive(archive, web_based, import_kwargs, migration)


def _echo_exception(msg: str, exception, warn_only: bool = False):
    """Correctly report and exception.

    :param msg: The message prefix
    :param exception: the exception raised
    :param warn_only: If True only print a warning, otherwise calls sys.exit with a non-zero exit status

    """
    from aiida.tools.importexport import IMPORT_LOGGER
    message = f'{msg}: {exception.__class__.__name__}: {str(exception)}'
    if warn_only:
        echo.echo_warning(message)
    else:
        IMPORT_LOGGER.debug('%s', traceback.format_exc())
        echo.echo_critical(message)


def _gather_imports(archives, webpages) -> List[Tuple[str, bool]]:
    """Gather archives to import and sort into local files and URLs.

    :returns: list of (archive path, whether it is web based)

    """
    from aiida.tools.importexport.common.utils import get_valid_import_links

    final_archives = []

    # Build list of archives to be imported
    for archive in archives:
        if archive.startswith('http://') or archive.startswith('https://'):
            final_archives.append((archive, True))
        else:
            final_archives.append((archive, False))

    # Discover and retrieve *.aiida files at URL(s)
    if webpages is not None:
        for webpage in webpages:
            try:
                echo.echo_info(f'retrieving archive URLS from {webpage}')
                urls = get_valid_import_links(webpage)
            except Exception as error:
                echo.echo_critical(
                    f'an exception occurred while trying to discover archives at URL {webpage}:\n{error}'
                )
            else:
                echo.echo_success(f'{len(urls)} archive URLs discovered and added')
                final_archives.extend([(u, True) for u in urls])

    return final_archives


def _import_archive(archive: str, web_based: bool, import_kwargs: dict, try_migration: bool):
    """Perform the archive import.

    :param archive: the path or URL to the archive
    :param web_based: If the archive needs to be downloaded first
    :param import_kwargs: keyword arguments to pass to the import function
    :param try_migration: whether to try a migration if the import raises IncompatibleArchiveVersionError

    """
    from aiida.common.folders import SandboxFolder
    from aiida.tools.importexport import (
        detect_archive_type, EXPORT_VERSION, import_data, IncompatibleArchiveVersionError
    )
    from aiida.tools.importexport.archive.migrators import get_migrator

    with SandboxFolder() as temp_folder:

        archive_path = archive

        if web_based:
            echo.echo_info(f'downloading archive: {archive}')
            try:
                response = urllib.request.urlopen(archive)
            except Exception as exception:
                _echo_exception(f'downloading archive {archive} failed', exception)
            temp_folder.create_file_from_filelike(response, 'downloaded_archive.zip')
            archive_path = temp_folder.get_abs_path('downloaded_archive.zip')
            echo.echo_success('archive downloaded, proceeding with import')

        echo.echo_info(f'starting import: {archive}')
        try:
            import_data(archive_path, **import_kwargs)
        except IncompatibleArchiveVersionError as exception:
            if try_migration:

                echo.echo_info(f'incompatible version detected for {archive}, trying migration')
                try:
                    migrator = get_migrator(detect_archive_type(archive_path))(archive_path)
                    archive_path = migrator.migrate(
                        EXPORT_VERSION, None, out_compression='none', work_dir=temp_folder.abspath
                    )
                except Exception as exception:
                    _echo_exception(f'an exception occurred while migrating the archive {archive}', exception)

                echo.echo_info('proceeding with import of migrated archive')
                try:
                    import_data(archive_path, **import_kwargs)
                except Exception as exception:
                    _echo_exception(
                        f'an exception occurred while trying to import the migrated archive {archive}', exception
                    )
            else:
                _echo_exception(f'an exception occurred while trying to import the archive {archive}', exception)
        except Exception as exception:
            _echo_exception(f'an exception occurred while trying to import the archive {archive}', exception)

        echo.echo_success(f'imported archive {archive}')
