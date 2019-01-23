# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi import` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from enum import Enum
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params.options import MultipleValueOption
from aiida.cmdline.params.types import GroupParamType
from aiida.cmdline.utils import decorators, echo
from aiida.common import exceptions

EXTRAS_IMPORT_MODES = ['keep_existing', 'update_existing', 'mirror', 'none', 'ask']


# pylint: disable=too-few-public-methods
class ExtrasImportCode(Enum):
    """Exit codes for the verdi command line."""
    keep_existing = 'kcl'
    update_existing = 'kcu'
    mirror = 'ncu'
    none = 'knl'
    ask = 'kca'


@verdi.command('import')
@click.argument('archives', nargs=-1, type=click.Path(exists=True, readable=True))
@click.option(
    '-w',
    '--webpages',
    type=click.STRING,
    cls=MultipleValueOption,
    help="Discover all URL targets pointing to files with the .aiida extension for these HTTP addresses. "
    "Automatically discovered archive URLs will be downloadeded and added to ARCHIVES for importing")
@click.option(
    '-G',
    '--group',
    type=GroupParamType(create_if_not_exist=True),
    help='Specify group to which all the import nodes will be added. If such a group does not exist, it will be'
    ' created automatically.')
@click.option(
    '-e',
    '--extras_import_mode',
    type=click.Choice(EXTRAS_IMPORT_MODES),
    default='keep_existing',
    help="keep_existing: in case of a name collision keep the original value. "
    "update_existing: in case of a name collision take the updated value. "
    "mirror: keep the imported extras only and remove the extras that are not present in the imported node. "
    "none: do not import the new extras. "
    "ask: ask what to do in case of a name collision. ")
@decorators.with_dbenv()
def cmd_import(archives, webpages, group, extras_import_mode):
    """Import one or multiple exported AiiDA archives

    The ARCHIVES can be specified by their relative or absolute file path, or their HTTP URL.
    """
    # pylint: disable=too-many-branches,too-many-statements,broad-except
    import traceback
    from six.moves import urllib

    from aiida.common.folders import SandboxFolder
    from aiida.orm.importexport import get_valid_import_links, import_data

    archives_url = []
    archives_file = []

    for archive in archives:
        if archive.startswith('http://') or archive.startswith('https://'):
            archives_url.append(archive)
        else:
            archives_file.append(archive)

    if webpages is not None:
        for webpage in webpages:
            try:
                echo.echo_info('retrieving archive URLS from {}'.format(webpage))
                urls = get_valid_import_links(webpage)
            except Exception:
                echo.echo_error('an exception occurred while trying to discover archives at URL {}'.format(webpage))
                echo.echo(traceback.format_exc())
                click.confirm('do you want to continue?', abort=True)
            else:
                echo.echo_success('{} archive URLs discovered and added'.format(len(urls)))
                archives_url += urls

    if not archives_url + archives_file:
        echo.echo_critical('no valid exported archives were found')

    for archive in archives_file:

        echo.echo_info('importing archive {}'.format(archive))

        try:
            import_data(archive, group, extras_mode=ExtrasImportCode[extras_import_mode].value)
        except exceptions.IncompatibleArchiveVersionError as exception:
            echo.echo_warning('{} cannot be imported: {}'.format(archive, exception))
            echo.echo_warning('run `verdi export migrate {}` to update it'.format(archive))
            continue
        except Exception:
            echo.echo_error('an exception occurred while importing the archive {}'.format(archive))
            echo.echo(traceback.format_exc())
            click.confirm('do you want to continue?', abort=True)
        else:
            echo.echo_success('imported archive {}'.format(archive))

    for archive in archives_url:

        echo.echo_info('downloading archive {}'.format(archive))

        try:
            response = urllib.request.urlopen(archive)
        except Exception as exception:
            echo.echo_warning('downloading archive {} failed: {}'.format(archive, exception))

        with SandboxFolder() as temp_folder:
            temp_file = 'importfile.tar.gz'
            temp_folder.create_file_from_filelike(response, temp_file)
            echo.echo_success('archive downloaded, proceeding with import')

            try:
                import_data(
                    temp_folder.get_abs_path(temp_file), group, extras_mode=ExtrasImportCode[extras_import_mode].value)
            except exceptions.IncompatibleArchiveVersionError as exception:
                echo.echo_warning('{} cannot be imported: {}'.format(archive, exception))
                echo.echo_warning('download the archive file and run `verdi export migrate` to update it')
                continue
            except Exception:
                echo.echo_error('an exception occurred while importing the archive {}'.format(archive))
                echo.echo(traceback.format_exc())
                click.confirm('do you want to continue?', abort=True)
            else:
                echo.echo_success('imported archive {}'.format(archive))
