# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data remote` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import click

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.params import arguments, types
from aiida.cmdline.utils import echo
from aiida.common.files import get_mode_string


@verdi_data.group('remote')
def remote():
    """Managing RemoteData objects."""


@remote.command('ls')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:remote',)))
@click.option('-l', '--long', 'ls_long', is_flag=True, default=False, help='Display also file metadata.')
@click.option('-p', '--path', type=click.STRING, default='.', help='The folder to list.')
def remote_ls(ls_long, path, datum):
    """List directory content on remote RemoteData objects."""
    import datetime
    try:
        content = datum.listdir_withattributes(path=path)
    except (IOError, OSError) as err:
        echo.echo_critical('Unable to access the remote folde or file, check if it exists.\n'
                           'Original error: {}'.format(str(err)))
    for metadata in content:
        if ls_long:
            mtime = datetime.datetime.fromtimestamp(metadata['attributes'].st_mtime)
            pre_line = '{} {:10}  {}  '.format(
                get_mode_string(metadata['attributes'].st_mode), metadata['attributes'].st_size,
                mtime.strftime("%d %b %Y %H:%M"))
            click.echo(pre_line, nl=False)
        if metadata['isdir']:
            click.echo(click.style(metadata['name'], fg='blue'))
        else:
            click.echo(metadata['name'])


@remote.command('cat')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:remote',)))
@click.argument('path', type=click.STRING)
def remote_cat(datum, path):
    """Show the content of remote files in RemoteData objects."""
    import os
    import sys
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmpf:
            tmpf.close()
            datum.getfile(path, tmpf.name)
            with io.open(tmpf.name, encoding='utf8') as fhandle:
                sys.stdout.write(fhandle.read())
    except IOError as err:
        echo.echo_critical('{}: {}'.format(err.errno, str(err)))

    try:
        os.remove(tmpf.name)
    except OSError:
        # If you cannot delete, ignore (maybe I didn't manage to create it in the first place
        pass


@remote.command('show')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:remote',)))
def remote_show(datum):
    """Show information on a RemoteData object."""
    click.echo('- Remote computer name:')
    click.echo('  {}'.format(datum.get_computer_name()))
    click.echo('- Remote folder full path:')
    click.echo('  {}'.format(datum.get_remote_path()))
