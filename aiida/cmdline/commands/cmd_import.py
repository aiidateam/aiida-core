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
# pylint: disable=broad-except,too-many-arguments,too-many-locals,too-many-branches
from enum import Enum
from typing import Tuple
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
    'Automatically discovered archive URLs will be downloadeded and added to ARCHIVES for importing'
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
    # pylint: disable=too-many-statements
    from aiida.common.folders import SandboxFolder
    from aiida.common.progress_reporter import set_progress_bar_tqdm, set_progress_reporter
    from aiida.tools.importexport.dbimport.utils import IMPORT_LOGGER
    from aiida.tools.importexport.archive.migrators import MIGRATE_LOGGER

    if verbosity in ['DEBUG', 'INFO']:
        set_progress_bar_tqdm(leave=(verbosity == 'DEBUG'))
    else:
        set_progress_reporter(None)
    IMPORT_LOGGER.setLevel(verbosity)
    MIGRATE_LOGGER.setLevel(verbosity)

    error = False

    archives_file, archives_url, gather_error = _gather_imports(archives, webpages, non_interactive)

    if gather_error:
        error = True

    # Preliminary sanity check
    if not archives_url + archives_file:
        echo.echo_critical('no valid exported archives were found')

    # Import initialization
    import_opts = {
        'file_to_import': '',
        'archive': '',
        'group': group,
        'migration': migration,
        'extras_mode_existing': ExtrasImportCode[extras_mode_existing].value,
        'extras_mode_new': extras_mode_new,
        'comment_mode': comment_mode,
        'non_interactive': non_interactive,
    }

    # Import local archives
    for archive in archives_file:

        echo.echo_info(f'importing archive {archive}')

        # Initialization
        import_error = False
        import_opts['archive'] = archive
        import_opts['file_to_import'] = import_opts['archive']
        import_opts['more_archives'] = archive != archives_file[-1] or archives_url

        # First attempt to import archive
        migrate_archive, import_error = _try_import(migration_performed=False, **import_opts)

        # Migrate archive if needed and desired
        if migrate_archive:
            with SandboxFolder() as temp_folder:
                import_opts['file_to_import'] = _migrate_archive(ctx, temp_folder, **import_opts)
                _, import_error = _try_import(migration_performed=True, **import_opts)

        if import_error:
            error = True

    # Import web-archives
    for archive in archives_url:

        # Initialization
        import_error = False
        import_opts['archive'] = archive
        import_opts['more_archives'] = archive != archives_url[-1]

        echo.echo_info(f'downloading archive {archive}')

        try:
            response = urllib.request.urlopen(archive)
        except Exception as exception:
            import_error = True
            _echo_error(f'downloading archive {archive} failed', raised_exception=exception, **import_opts)
            continue

        with SandboxFolder() as temp_folder:
            temp_file = 'importfile.tar.gz'

            # Download archive to temporary file
            temp_folder.create_file_from_filelike(response, temp_file)
            echo.echo_success('archive downloaded, proceeding with import')

            # First attempt to import archive
            import_opts['file_to_import'] = temp_folder.get_abs_path(temp_file)
            migrate_archive, import_error = _try_import(migration_performed=False, **import_opts)

            # Migrate archive if needed and desired
            if migrate_archive:
                import_opts['file_to_import'] = _migrate_archive(ctx, temp_folder, **import_opts)
                _, import_error = _try_import(migration_performed=True, **import_opts)

        if import_error:
            error = True

    if error:
        return 1


def _gather_imports(archives, webpages, non_interactive) -> Tuple[list, list, bool]:
    """Gather archives to import and sort into local and web-base.

    :returns: (file archive, web archives, whether an error occurred)

    """
    from aiida.tools.importexport.common.utils import get_valid_import_links

    archives_url = []
    archives_file = []
    error = False

    # Build list of archives to be imported
    for archive in archives:
        if archive.startswith('http://') or archive.startswith('https://'):
            archives_url.append(archive)
        else:
            archives_file.append(archive)

    # Discover and retrieve *.aiida files at URL(s)
    if webpages is not None:
        for webpage in webpages:
            try:
                echo.echo_info(f'retrieving archive URLS from {webpage}')
                urls = get_valid_import_links(webpage)
            except Exception as exception:
                _echo_error(
                    f'an exception occurred while trying to discover archives at URL {webpage}',
                    non_interactive=non_interactive,
                    more_archives=webpage != webpages[-1] or archives_file or archives_url,
                    raised_exception=exception
                )
                error = True
            else:
                echo.echo_success(f'{len(urls)} archive URLs discovered and added')
                archives_url += urls

    return archives_file, archives_url, error


def _try_import(migration_performed, file_to_import, archive, group, migration, non_interactive, **kwargs):
    """Utility function for `verdi import` to try to import archive

    :param migration_performed: Boolean to determine the exception message to throw for
        `~aiida.tools.importexport.common.exceptions.IncompatibleArchiveVersionError`
    :param file_to_import: Absolute path, including filename, of file to be migrated.
    :param archive: Filename of archive to be migrated, and later attempted imported.
    :param group: AiiDA Group into which the import will be associated.
    :param migration: Whether or not to force migration of archive, if needed.
    :param non_interactive: Whether or not the user should be asked for input for any reason.
    :param kwargs: Key-word-arguments that _must_ contain:
        * `'extras_mode_existing'`: `import_data`'s `'extras_mode_existing'` keyword, determining import rules for
        Extras.
        * `'extras_mode_new'`: `import_data`'s `'extras_mode_new'` keyword, determining import rules for Extras.
        * `'comment_mode'`: `import_data`'s `'comment_mode'` keyword, determining import rules for Comments.
    """
    from aiida.common.log import override_log_formatter_context
    from aiida.tools.importexport import import_data, IncompatibleArchiveVersionError

    # Checks
    expected_keys = ['extras_mode_existing', 'extras_mode_new', 'comment_mode']
    for key in expected_keys:
        if key not in kwargs:
            raise ValueError(f"{key} needed for utility function '_try_import' to use in 'import_data'")

    # Initialization
    migrate_archive = False
    error = False

    try:
        with override_log_formatter_context('%(message)s'):
            import_data(file_to_import, group, **kwargs)
    except IncompatibleArchiveVersionError as exception:
        error = True
        if migration_performed:
            # Migration has been performed, something is still wrong
            _echo_error(
                f'{archive} has been migrated, but it still cannot be imported',
                non_interactive=non_interactive,
                raised_exception=exception,
                **kwargs
            )
        else:
            # Migration has not yet been tried.
            if migration:
                # Confirm migration
                echo.echo_warning(str(exception).splitlines()[0])
                if non_interactive:
                    migrate_archive = True
                else:
                    migrate_archive = click.confirm(
                        'Do you want to try and migrate {} to the newest archive file version?\n'
                        'Note: This will not change your current file.'.format(archive),
                        default=True,
                        abort=True
                    )
            else:
                # Abort
                echo.echo_critical(str(exception))
    except Exception as exception:
        error = True
        _echo_error(
            f'an exception occurred while importing the archive {archive}',
            non_interactive=non_interactive,
            raised_exception=exception,
            **kwargs
        )
    else:
        echo.echo_success(f'imported archive {archive}')

    return migrate_archive, error


def _migrate_archive(ctx, temp_folder, file_to_import, archive, non_interactive, more_archives, **kwargs):  # pylint: disable=unused-argument
    """Utility function for `verdi import` to migrate archive
    Invoke click command `verdi export migrate`, passing in the archive,
    outputting the migrated archive in a temporary SandboxFolder.
    Try again to import the now migrated file, after a successful migration.

    :param ctx: Click context used to invoke `verdi export migrate`.
    :param temp_folder: SandboxFolder, where the migrated file will be temporarily outputted.
    :param file_to_import: Absolute path, including filename, of file to be migrated.
    :param archive: Filename of archive to be migrated, and later attempted imported.
    :param non_interactive: Whether or not the user should be asked for input for any reason.
    :param more_archives: Whether or not there are more archives to be imported.
    :param silent: Suppress console messages.
    :return: Absolute path to migrated archive within SandboxFolder.
    """
    from aiida.common.log import override_log_formatter_context
    from aiida.tools.importexport import detect_archive_type, EXPORT_VERSION
    from aiida.tools.importexport.archive.migrators import get_migrator

    # Echo start
    echo.echo_info(f'migrating archive {archive}')

    # Initialization
    temp_out_file = 'migrated_importfile.aiida'

    # Migration
    try:
        migrator_cls = get_migrator(detect_archive_type(file_to_import))
        migrator = migrator_cls(file_to_import)
        with override_log_formatter_context('%(message)s'):
            migrator.migrate(EXPORT_VERSION, temp_folder.get_abs_path(temp_out_file), out_compression='zip')
    except Exception as exception:
        _echo_error(
            f'an exception occurred while migrating the archive: {archive}.\n'
            "Use 'verdi export migrate' to update this archive file.",
            non_interactive=non_interactive,
            more_archives=more_archives,
            raised_exception=exception
        )
    else:
        # Success
        echo.echo_info('proceeding with import')

        return temp_folder.get_abs_path(temp_out_file)


def _echo_error(  # pylint: disable=unused-argument
    message, non_interactive, more_archives, raised_exception, **kwargs
):
    """Utility function to help write an error message for ``verdi import``

    :param message: Message following red-colored, bold "Error:".
    :type message: str
    :param non_interactive: Whether or not the user should be asked for input for any reason.
    :type non_interactive: bool
    :param more_archives: Whether or not there are more archives to import.
    :type more_archives: bool
    :param raised_exception: Exception raised during error.
    :type raised_exception: `Exception`
    """
    from aiida.tools.importexport import IMPORT_LOGGER

    IMPORT_LOGGER.debug('%s', traceback.format_exc())

    exception = f'{raised_exception.__class__.__name__}: {str(raised_exception)}'

    echo.echo_error(message)
    echo.echo(exception)

    if more_archives:
        # There are more archives to go through
        if non_interactive:
            # Continue to next archive
            pass
        else:
            # Ask if one should continue to next archive
            click.confirm('Do you want to continue?', abort=True)
    else:
        # There are no more archives
        click.Abort()
