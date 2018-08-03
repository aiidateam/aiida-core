# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This allows to manage ParameterData objects from command line.
"""
import click
from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.params import arguments
from aiida.cmdline.utils import echo
from aiida.common.utils import get_mode_string


@verdi_data.group('remote')
def remote():
    """
    Managing Remote_Data data types
    """
    pass


@remote.command('ls')
@click.option('-l', '--long', 'ls_long', is_flag=True, default=False, help="Display also file metadata")
@click.option('-p', '--path', type=click.STRING, default='.', help="The folder to list")
@arguments.NODE()
def lsfunction(ls_long, path, node):
    """
    List directory content on remote RemoteData objects.
    """
    import datetime
    try:
        content = node.listdir_withattributes(path=path)
    except (IOError, OSError) as err:
        echo.echo_critical("Unable to access the remote folder"
                           " or file, check if it exists.\n"
                           "Original error: {}".format(str(err)))
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
@arguments.NODE()
@click.argument('path', type=click.STRING)
def cat(node, path):
    """
    Show the content of remote files in RemoteData objects.
    """
    import os
    import sys
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmpf:
            tmpf.close()
            node.getfile(path, tmpf.name)
            with open(tmpf.name) as fobj:
                sys.stdout.write(fobj.read())
    except IOError as err:
        click.echo("ERROR {}: {}".format(err.errno, str(err)), err=True)
        sys.exit(1)

    try:
        os.remove(tmpf.name)
    except OSError:
        # If you cannot delete, ignore (maybe I didn't manage to create it in the first place
        pass


@remote.command('show')
@arguments.NODE()
def show(node):
    """
    Show information on a RemoteData object.
    """
    click.echo("- Remote computer name:")
    click.echo("  {}".format(node.get_computer_name()))
    click.echo("- Remote folder full path:")
    click.echo("  {}".format(node.get_remote_path()))
