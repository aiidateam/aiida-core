###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi archive` command."""

import logging
import traceback
from enum import Enum
from pathlib import Path
from typing import List, Tuple

import click
from click_spinner import spinner

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.params.types import GroupParamType, PathOrUrl
from aiida.cmdline.utils import decorators, echo
from aiida.common.exceptions import CorruptStorage, IncompatibleStorageSchema, UnreachableStorage
from aiida.common.links import GraphTraversalRules
from aiida.common.log import AIIDA_LOGGER
from aiida.common.utils import DEFAULT_BATCH_SIZE

EXTRAS_MODE_EXISTING = ['keep_existing', 'update_existing', 'mirror', 'none']
EXTRAS_MODE_NEW = ['import', 'none']
COMMENT_MODE = ['leave', 'newest', 'overwrite']


@verdi.group('archive')
def verdi_archive():
    """Create, inspect and import AiiDA archives."""


@verdi_archive.command('version')
@click.argument('path', nargs=1, type=click.Path(exists=True, readable=True))
def archive_version(path):
    """Print the current version of an archive's schema."""
    # note: this mirrors `cmd_storage:storage_version`
    # it is currently hardcoded to the `SqliteZipBackend`, but could be generalized in the future
    from aiida.storage.sqlite_zip.backend import SqliteZipBackend

    storage_cls = SqliteZipBackend
    profile = storage_cls.create_profile(path)
    head_version = storage_cls.version_head()
    try:
        profile_version = storage_cls.version_profile(profile)
    except (UnreachableStorage, CorruptStorage) as exc:
        echo.echo_critical(f'archive file version unreadable: {exc}')
    echo.echo(f'Latest archive schema version: {head_version!r}')
    echo.echo(f'Archive schema version of {Path(path).name!r}: {profile_version!r}')


@verdi_archive.command('info')
@click.argument('path', nargs=1, type=click.Path(exists=True, readable=True))
@click.option('--detailed', is_flag=True, help='Provides more detailed information.')
def archive_info(path, detailed):
    """Summarise the contents of an archive."""
    # note: this mirrors `cmd_storage:storage_info`
    # it is currently hardcoded to the `SqliteZipBackend`, but could be generalized in the future
    from aiida.storage.sqlite_zip.backend import SqliteZipBackend

    try:
        storage = SqliteZipBackend(SqliteZipBackend.create_profile(path))
    except (UnreachableStorage, CorruptStorage) as exc:
        echo.echo_critical(f'archive file unreadable: {exc}')
    except IncompatibleStorageSchema as exc:
        echo.echo_critical(f'archive version incompatible: {exc}')
    with spinner():
        try:
            data = storage.get_info(detailed=detailed)
        finally:
            storage.close()

    echo.echo_dictionary(data, sort_keys=False, fmt='yaml')


@verdi_archive.command(
    'inspect', hidden=True, deprecated='Use `verdi archive version` or `verdi archive info` instead.'
)
@click.argument('archive', nargs=1, type=click.Path(exists=True, readable=True))
@click.option('-v', '--version', is_flag=True, help='Print the archive format version and exit.')
@click.option('-m', '--meta-data', is_flag=True, help='Print the meta data contents and exit.')
@click.option('-d', '--database', is_flag=True, help='Include information on entities in the database.')
@click.pass_context
def inspect(ctx, archive, version, meta_data, database):
    """Inspect contents of an archive without importing it.

    .. deprecated:: v2.0.0, use `verdi archive version` or `verdi archive info` instead.
    """
    if version:
        ctx.invoke(archive_version, path=archive)
    elif database:
        ctx.invoke(archive_info, path=archive, detailed=True)
    else:
        ctx.invoke(archive_info, path=archive, detailed=False)


@verdi_archive.command('create')
@arguments.OUTPUT_FILE(type=click.Path(exists=False))
@options.ALL()
@options.CODES()
@options.COMPUTERS()
@options.GROUPS()
@options.NODES()
@options.FORCE(help='Overwrite output file if it already exists.')
@options.graph_traversal_rules(GraphTraversalRules.EXPORT.value)
@click.option(
    '--include-logs/--exclude-logs',
    default=True,
    show_default=True,
    help='Include or exclude logs for node(s) in export.',
)
@click.option(
    '--include-comments/--exclude-comments',
    default=True,
    show_default=True,
    help='Include or exclude comments for node(s) in export. (Will also export extra users who commented).',
)
@click.option(
    '--include-authinfos/--exclude-authinfos',
    default=False,
    show_default=True,
    help='Include or exclude authentication information for computer(s) in export.',
)
@click.option('--compress', default=6, show_default=True, type=int, help='Level of compression to use (0-9).')
@click.option(
    '-b',
    '--batch-size',
    default=DEFAULT_BATCH_SIZE,
    type=int,
    help='Stream database rows in batches, to reduce memory usage.',
)
@click.option(
    '--test-run',
    is_flag=True,
    help='Determine entities to export, but do not create the archive. Deprecated, please use `--dry-run` instead.',
)
@options.DRY_RUN(help='Determine entities to export, but do not create the archive.')
@decorators.with_dbenv()
def create(
    output_file,
    all_entries,
    codes,
    computers,
    groups,
    nodes,
    force,
    input_calc_forward,
    input_work_forward,
    create_backward,
    return_backward,
    call_calc_backward,
    call_work_backward,
    include_comments,
    include_logs,
    include_authinfos,
    compress,
    batch_size,
    test_run,
    dry_run,
):
    """Create an archive from all or part of a profiles's data.

    Besides Nodes of the provenance graph, you can archive Groups, Codes, Computers, Comments and Logs.

    By default, the archive file will include not only the entities explicitly provided via the command line but also
    their provenance, according to the rules outlined in the documentation.
    You can modify some of those rules using options of this command.
    """
    from aiida.common.progress_reporter import set_progress_bar_tqdm, set_progress_reporter
    from aiida.tools.archive.abstract import get_format
    from aiida.tools.archive.create import create_archive
    from aiida.tools.archive.exceptions import ArchiveExportError

    archive_format = get_format()

    if test_run:
        echo.echo_deprecated('the `--test-run` option is deprecated. Use `-n/--dry-run` option instead')
        dry_run = test_run

    if all_entries:
        entities = None
    else:
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
        'include_authinfos': include_authinfos,
        'include_comments': include_comments,
        'include_logs': include_logs,
        'overwrite': force,
        'compression': compress,
        'batch_size': batch_size,
        'test_run': dry_run,
    }

    if AIIDA_LOGGER.level <= logging.REPORT:
        set_progress_bar_tqdm(leave=AIIDA_LOGGER.level <= logging.INFO)
    else:
        set_progress_reporter(None)

    try:
        create_archive(entities, filename=output_file, archive_format=archive_format, **kwargs)
    except ArchiveExportError as exception:
        echo.echo_critical(f'failed to write the archive file: {exception}')
    else:
        if not dry_run:
            echo.echo_success(f'wrote the export archive file to {output_file}')


@verdi_archive.command('migrate')
@arguments.INPUT_FILE()
@arguments.OUTPUT_FILE(required=False)
@options.FORCE(help='overwrite output file if it already exists')
@click.option('-i', '--in-place', is_flag=True, help='Migrate the archive in place, overwriting the original file.')
@click.option(
    '--version',
    type=click.STRING,
    required=False,
    metavar='VERSION',
    # Note: Adding aiida.tools.EXPORT_VERSION as a default value explicitly would result in a slow import of
    # aiida.tools and, as a consequence, aiida.orm. As long as this is the case, better determine the latest export
    # version inside the function when needed.
    help='Archive format version to migrate to (defaults to latest version).',
)
def migrate(input_file, output_file, force, in_place, version):
    """Migrate an archive to a more recent schema version."""
    from aiida.common.progress_reporter import set_progress_bar_tqdm, set_progress_reporter
    from aiida.tools.archive.abstract import get_format

    if in_place:
        if output_file:
            echo.echo_critical('output file specified together with --in-place flag')
        output_file = input_file
        force = True
    elif not output_file:
        echo.echo_critical(
            'no output file specified. Please add --in-place flag if you would like to migrate in place.'
        )

    if AIIDA_LOGGER.level <= logging.REPORT:
        set_progress_bar_tqdm(leave=AIIDA_LOGGER.level <= logging.INFO)
    else:
        set_progress_reporter(None)

    archive_format = get_format()

    if version is None:
        version = archive_format.latest_version

    try:
        archive_format.migrate(input_file, output_file, version, force=force, compression=6)
    except Exception as error:
        if AIIDA_LOGGER.level <= logging.DEBUG:
            raise
        echo.echo_critical(
            'failed to migrate the archive file (use `--verbosity DEBUG` to see traceback): '
            f'{error.__class__.__name__}:{error}'
        )

    echo.echo_success(f'migrated the archive to version {version!r}')


class ExtrasImportCode(Enum):
    """Exit codes for the verdi command line."""

    keep_existing = ('k', 'c', 'l')
    update_existing = ('k', 'c', 'u')
    mirror = ('n', 'c', 'u')
    none = ('k', 'n', 'l')


@verdi_archive.command('import')
@click.argument('archives', nargs=-1, type=PathOrUrl(exists=True, readable=True))
@click.option(
    '-w',
    '--webpages',
    type=click.STRING,
    cls=options.MultipleValueOption,
    help='Discover all URL targets pointing to files with the .aiida extension for these HTTP addresses. '
    'Automatically discovered archive URLs will be downloaded and added to ARCHIVES for importing.',
)
@click.option(
    '--import-group/--no-import-group',
    default=True,
    show_default=True,
    help='Add all imported nodes to the specified group, or an automatically created one',
)
@options.GROUP(
    type=GroupParamType(create_if_not_exist=True),
    help='Specify group to which all the import nodes will be added. If such a group does not exist, it will be'
    ' created automatically.',
)
@click.option(
    '-e',
    '--extras-mode-existing',
    type=click.Choice(EXTRAS_MODE_EXISTING),
    default='none',
    help='Specify which extras from the export archive should be imported for nodes that are already contained in the '
    'database: '
    'none: do not import any extras.'
    'keep_existing: import all extras and keep original value of existing extras. '
    'update_existing: import all extras and overwrite value of existing extras. '
    'mirror: import all extras and remove any existing extras that are not present in the archive. ',
)
@click.option(
    '--extras-mode-new',
    type=click.Choice(EXTRAS_MODE_NEW),
    default='import',
    help='Specify whether to import extras of new nodes: ' 'import: import extras. ' 'none: do not import extras.',
)
@click.option(
    '--comment-mode',
    type=click.Choice(COMMENT_MODE),
    default='leave',
    help='Specify the way to import Comments with identical UUIDs: '
    'leave: Leave the existing Comments in the database (default).'
    'newest: Use only the newest Comments (based on mtime).'
    'overwrite: Replace existing Comments with those from the import file.',
)
@click.option(
    '--include-authinfos/--exclude-authinfos',
    default=False,
    show_default=True,
    help='Include or exclude authentication information for computer(s) in import.',
)
@click.option(
    '--migration/--no-migration',
    default=True,
    show_default=True,
    help='Force migration of archive file archives, if needed.',
)
@click.option(
    '-b', '--batch-size', default=1000, type=int, help='Stream database rows in batches, to reduce memory usage.'
)
@click.option(
    '--test-run',
    is_flag=True,
    help='Determine entities to import, but do not actually import them. Deprecated, please use `--dry-run` instead.',
)
@options.DRY_RUN(help='Determine entities to import, but do not actually import them.')
@decorators.with_dbenv()
@click.pass_context
def import_archive(
    ctx,
    archives,
    webpages,
    extras_mode_existing,
    extras_mode_new,
    comment_mode,
    include_authinfos,
    migration,
    batch_size,
    import_group,
    group,
    test_run,
    dry_run,
):
    """Import archived data to a profile.

    The archive can be specified by its relative or absolute file path, or its HTTP URL.
    """
    from aiida.common.progress_reporter import set_progress_bar_tqdm, set_progress_reporter

    if test_run:
        echo.echo_deprecated('the `--test-run` option is deprecated. Use `-n/--dry-run` option instead')
        dry_run = test_run

    if AIIDA_LOGGER.level <= logging.REPORT:
        set_progress_bar_tqdm(leave=AIIDA_LOGGER.level <= logging.INFO)
    else:
        set_progress_reporter(None)

    all_archives = _gather_imports(archives, webpages)

    # Preliminary sanity check
    if not all_archives:
        echo.echo_critical('no valid exported archives were found')

    # Shared import key-word arguments
    import_kwargs = {
        'import_new_extras': extras_mode_new == 'import',
        'merge_extras': ExtrasImportCode[extras_mode_existing].value,
        'merge_comments': comment_mode,
        'include_authinfos': include_authinfos,
        'batch_size': batch_size,
        'create_group': import_group,
        'group': group,
        'test_run': dry_run,
    }

    for archive, web_based in all_archives:
        _import_archive_and_migrate(ctx, archive, web_based, import_kwargs, migration)


def _echo_exception(msg: str, exception, warn_only: bool = False):
    """Correctly report and exception.

    :param msg: The message prefix
    :param exception: the exception raised
    :param warn_only: If True only print a warning, otherwise calls sys.exit with a non-zero exit status

    """
    from aiida.tools.archive.imports import IMPORT_LOGGER

    message = f'{msg}: {exception.__class__.__name__}: {exception!s}'
    if warn_only:
        echo.echo_warning(message)
    else:
        IMPORT_LOGGER.info('%s', traceback.format_exc())
        echo.echo_critical(message)


def _gather_imports(archives, webpages) -> List[Tuple[str, bool]]:
    """Gather archives to import and sort into local files and URLs.

    :returns: list of (archive path, whether it is web based)

    """
    from aiida.tools.archive.common import get_valid_import_links

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
                echo.echo_report(f'retrieving archive URLS from {webpage}')
                urls = get_valid_import_links(webpage)
            except Exception as error:
                echo.echo_critical(
                    f'an exception occurred while trying to discover archives at URL {webpage}:\n{error}'
                )
            else:
                echo.echo_success(f'{len(urls)} archive URLs discovered and added')
                final_archives.extend([(u, True) for u in urls])

    return final_archives


def _import_archive_and_migrate(
    ctx: click.Context, archive: str, web_based: bool, import_kwargs: dict, try_migration: bool
):
    """Perform the archive import.

    :param archive: the path or URL to the archive
    :param web_based: If the archive needs to be downloaded first
    :param import_kwargs: keyword arguments to pass to the import function
    :param try_migration: whether to try a migration if the import raises `IncompatibleStorageSchema`

    """
    import urllib.request

    from aiida.common.folders import SandboxFolder
    from aiida.tools.archive.abstract import get_format
    from aiida.tools.archive.exceptions import ImportTestRun
    from aiida.tools.archive.imports import import_archive as _import_archive

    archive_format = get_format()
    filepath = ctx.obj['config'].get_option('storage.sandbox') or None
    dry_run_success = f'import dry-run of archive {archive} completed. Profile storage unmodified.'

    with SandboxFolder(filepath=filepath) as temp_folder:
        archive_path = archive

        if web_based:
            echo.echo_report(f'downloading archive: {archive}')
            try:
                with urllib.request.urlopen(archive) as response:
                    temp_folder.create_file_from_filelike(response, 'downloaded_archive.zip')
            except Exception as exception:
                _echo_exception(f'downloading archive {archive} failed', exception)

            archive_path = temp_folder.get_abs_path('downloaded_archive.zip')
            echo.echo_success('archive downloaded, proceeding with import')

        echo.echo_report(f'starting import: {archive}')
        try:
            _import_archive(archive_path, archive_format=archive_format, **import_kwargs)
        except IncompatibleStorageSchema as exception:
            if try_migration:
                echo.echo_report(f'incompatible version detected for {archive}, trying migration')
                try:
                    new_path = temp_folder.get_abs_path('migrated_archive.aiida')
                    archive_format.migrate(archive_path, new_path, archive_format.latest_version, compression=0)
                    archive_path = new_path
                except Exception as sub_exception:
                    _echo_exception(f'an exception occurred while migrating the archive {archive}', sub_exception)

                echo.echo_report('proceeding with import of migrated archive')
                try:
                    _import_archive(archive_path, archive_format=archive_format, **import_kwargs)
                except ImportTestRun:
                    echo.echo_success(dry_run_success)
                    return
                except Exception as sub_exception:
                    _echo_exception(
                        f'an exception occurred while trying to import the migrated archive {archive}', sub_exception
                    )
            else:
                _echo_exception(f'an exception occurred while trying to import the archive {archive}', exception)
        except ImportTestRun:
            echo.echo_success(dry_run_success)
            return

        except Exception as exception:
            _echo_exception(f'an exception occurred while trying to import the archive {archive}', exception)

        echo.echo_success(f'imported archive {archive}')
