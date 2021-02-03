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
# pylint: disable=broad-except
from enum import Enum
from typing import List, Tuple
import traceback
import urllib.request

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.params.types import GroupParamType, PathOrUrl
from aiida.cmdline.utils import decorators, echo

EXTRAS_MODE_EXISTING = ['keep_existing', 'update_existing', 'mirror', 'none', 'ask']
EXTRAS_MODE_NEW = ['import', 'none']
COMMENT_MODE = ['newest', 'overwrite']


class ExtrasImportCode(Enum):
    """Exit codes for the verdi command line."""
    keep_existing = 'kcl'
    update_existing = 'kcu'
    mirror = 'ncu'
    none = 'knl'
    ask = 'kca'


@verdi.command('import')
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
