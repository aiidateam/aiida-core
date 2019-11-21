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
import traceback
import urllib
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import options
from aiida.cmdline.params.types import GroupParamType, ImportPath
from aiida.cmdline.utils import decorators, echo

EXTRAS_MODE_EXISTING = ['keep_existing', 'update_existing', 'mirror', 'none', 'ask']
EXTRAS_MODE_NEW = ['import', 'none']
COMMENT_MODE = ['newest', 'overwrite']


# pylint: disable=too-few-public-methods
class ExtrasImportCode(Enum):
    """Exit codes for the verdi command line."""
    keep_existing = 'kcl'
    update_existing = 'kcu'
    mirror = 'ncu'
    none = 'knl'
    ask = 'kca'


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
    from aiida.tools.importexport import import_data, IncompatibleArchiveVersionError

    # Checks
    expected_keys = ['extras_mode_existing', 'extras_mode_new', 'comment_mode']
    for key in expected_keys:
        if key not in kwargs:
            raise ValueError("{} needed for utility function '{}' to use in 'import_data'".format(key, '_try_import'))

    # Initialization
    migrate_archive = False

    try:
        import_data(file_to_import, group, **kwargs)
    except IncompatibleArchiveVersionError as exception:
        if migration_performed:
            # Migration has been performed, something is still wrong
            crit_message = '{} has been migrated, but it still cannot be imported.\n{}'.format(archive, exception)
            echo.echo_critical(crit_message)
        else:
            # Migration has not yet been tried.
            if migration:
                # Confirm migration
                echo.echo_warning(str(exception).splitlines()[0])
                if non_interactive:
                    migrate_archive = True
                else:
                    migrate_archive = click.confirm(
                        'Do you want to try and migrate {} to the newest export file version?\n'
                        'Note: This will not change your current file.'.format(archive),
                        default=True,
                        abort=True
                    )
            else:
                # Abort
                echo.echo_critical(str(exception))
    except Exception:
        echo.echo_error('an exception occurred while importing the archive {}'.format(archive))
        echo.echo(traceback.format_exc())
        if not non_interactive:
            click.confirm('do you want to continue?', abort=True)
    else:
        echo.echo_success('imported archive {}'.format(archive))

    return migrate_archive


def _migrate_archive(ctx, temp_folder, file_to_import, archive, non_interactive, **kwargs):  # pylint: disable=unused-argument
    """Utility function for `verdi import` to migrate archive
    Invoke click command `verdi export migrate`, passing in the archive,
    outputting the migrated archive in a temporary SandboxFolder.
    Try again to import the now migrated file, after a successful migration.

    :param ctx: Click context used to invoke `verdi export migrate`.
    :param temp_folder: SandboxFolder, where the migrated file will be temporarily outputted.
    :param file_to_import: Absolute path, including filename, of file to be migrated.
    :param archive: Filename of archive to be migrated, and later attempted imported.
    :param non_interactive: Whether or not the user should be asked for input for any reason.
    :return: Absolute path to migrated archive within SandboxFolder.
    """
    from aiida.cmdline.commands.cmd_export import migrate

    # Echo start
    echo.echo_info('migrating archive {}'.format(archive))

    # Initialization
    temp_out_file = 'migrated_importfile.aiida'

    # Migration
    try:
        ctx.invoke(
            migrate, input_file=file_to_import, output_file=temp_folder.get_abs_path(temp_out_file), silent=False
        )
    except Exception:
        echo.echo_error(
            'an exception occurred while migrating the archive {}.\n'
            "Use 'verdi export migrate' to update this export file.".format(archive)
        )
        echo.echo(traceback.format_exc())
        if not non_interactive:
            click.confirm('do you want to continue?', abort=True)
    else:
        echo.echo_success('archive migrated, proceeding with import')

        return temp_folder.get_abs_path(temp_out_file)


@verdi.command('import')
@click.argument('archives', nargs=-1, type=ImportPath(exists=True, readable=True))
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
    help='Force migration of export file archives, if needed.'
)
@options.NON_INTERACTIVE()
@decorators.with_dbenv()
@click.pass_context
def cmd_import(
    ctx, archives, webpages, group, extras_mode_existing, extras_mode_new, comment_mode, migration, non_interactive
):
    """Import data from an AiiDA archive file.

    The archive can be specified by its relative or absolute file path, or its HTTP URL.
    """

    from aiida.common.folders import SandboxFolder
    from aiida.tools.importexport.common.utils import get_valid_import_links

    archives_url = []
    archives_file = []

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
                echo.echo_info('retrieving archive URLS from {}'.format(webpage))
                urls = get_valid_import_links(webpage)
            except Exception:
                echo.echo_error('an exception occurred while trying to discover archives at URL {}'.format(webpage))
                echo.echo(traceback.format_exc())
                if not non_interactive:
                    click.confirm('do you want to continue?', abort=True)
            else:
                echo.echo_success('{} archive URLs discovered and added'.format(len(urls)))
                archives_url += urls

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
        'non_interactive': non_interactive
    }

    # Import local archives
    for archive in archives_file:

        echo.echo_info('importing archive {}'.format(archive))

        # Initialization
        import_opts['archive'] = archive
        import_opts['file_to_import'] = import_opts['archive']

        # First attempt to import archive
        migrate_archive = _try_import(migration_performed=False, **import_opts)

        # Migrate archive if needed and desired
        if migrate_archive:
            with SandboxFolder() as temp_folder:
                import_opts['file_to_import'] = _migrate_archive(ctx, temp_folder, **import_opts)
                _try_import(migration_performed=True, **import_opts)

    # Import web-archives
    for archive in archives_url:

        # Initialization
        import_opts['archive'] = archive

        echo.echo_info('downloading archive {}'.format(archive))

        try:
            response = urllib.request.urlopen(archive)
        except Exception as exception:
            echo.echo_warning('downloading archive {} failed: {}'.format(archive, exception))

        with SandboxFolder() as temp_folder:
            temp_file = 'importfile.tar.gz'

            # Download archive to temporary file
            temp_folder.create_file_from_filelike(response, temp_file)
            echo.echo_success('archive downloaded, proceeding with import')

            # First attempt to import archive
            import_opts['file_to_import'] = temp_folder.get_abs_path(temp_file)
            migrate_archive = _try_import(migration_performed=False, **import_opts)

            # Migrate archive if needed and desired
            if migrate_archive:
                import_opts['file_to_import'] = _migrate_archive(ctx, temp_folder, **import_opts)
                _try_import(migration_performed=True, **import_opts)
