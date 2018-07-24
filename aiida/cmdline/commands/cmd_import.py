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
import click

from aiida.cmdline.baseclass import VerdiCommand
from aiida.cmdline.commands import verdi_import
from aiida.cmdline.params.options import MultipleValueOption
from aiida.cmdline.utils import decorators, echo


class Import(VerdiCommand):
    """
    Import AiiDA export archives
    """

    def run(self, *args):
        ctx = cmd_import.make_context('cmd_import', list(args))
        with ctx:
            cmd_import.invoke(ctx)


@verdi_import.command('import')
@click.argument('archives', nargs=-1, type=click.Path(exists=True, readable=True))
@click.option(
    '-w',
    '--webpages',
    type=click.STRING,
    cls=MultipleValueOption,
    help="Discover all URL targets pointing to files with the .aiida extension for these HTTP addresses. "
    "Automatically discovered archive URLs will be downloadeded and added to ARCHIVES for importing")
@decorators.with_dbenv()
def cmd_import(archives, webpages):
    """
    Import one or multiple exported AiiDA ARCHIVES specified by their relative or absolute file path, or their HTTP URL.
    """
    # pylint: disable=too-many-branches,broad-except
    import traceback
    import urllib2

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
        try:
            echo.echo_info('importing archive {}'.format(archive))
            import_data(archive)
        except Exception:
            echo.echo_error('an exception occurred while importing the archive {}'.format(archive))
            echo.echo(traceback.format_exc())
            click.confirm('do you want to continue?', abort=True)
        else:
            echo.echo_success('imported archive {}'.format(archive))

    for archive in archives_url:
        try:
            echo.echo_info('downloading archive {}'.format(archive))

            response = urllib2.urlopen(archive)

            with SandboxFolder() as temp_folder:
                temp_file = 'importfile.tar.gz'
                temp_folder.create_file_from_filelike(response, temp_file)
                echo.echo_success('archive downloaded, proceeding with import')
                import_data(temp_folder.get_abs_path(temp_file))

        except Exception:
            echo.echo_error('an exception occurred while importing the archive {}'.format(archive))
            echo.echo(traceback.format_exc())
            click.confirm('do you want to continue?', abort=True)
        else:
            echo.echo_success('imported archive {}'.format(archive))
