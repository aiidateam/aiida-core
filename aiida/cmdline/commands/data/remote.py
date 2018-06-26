# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import click
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import verdi, verdi_data
from aiida.cmdline.params import arguments
from aiida.cmdline.params import options
from aiida.cmdline.utils import echo
from aiida.common.exceptions import DanglingLinkError
from aiida.common.utils import get_mode_string


if not is_dbenv_loaded():
    load_dbenv()
        
@verdi_data.group('remote')
@click.pass_context
def remote(ctx):
    """help"""
    pass
    

@remote.command('ls')
@click.option('-l', '--long', is_flag=True, default=False,
              help="Display also file metadata")
@click.option('-p', '--path', type=click.STRING,
              default='.',
              help="The folder to list")
@arguments.NODE()
def ls(long, path, node):
    """
    List directory content on remote RemoteData objects.
    """
    try:
        content = node.listdir_withattributes(path=path)
    except (IOError, OSError) as e:
        echo.echo_critical("Unable to access the remote folder"
            " or file, check if it exists.\n"
            "Original error: {}".format(str(e)))
    for metadata in content:
        if long:
            mtime = datetime.datetime.fromtimestamp(
                metadata['attributes'].st_mtime)
            pre_line = '{} {:10}  {}  '.format(
                get_mode_string(metadata['attributes'].st_mode),
                metadata['attributes'].st_size,
                mtime.strftime("%d %b %Y %H:%M")
            )
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
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.close()
            node.getfile(path, f.name)
            with open(f.name) as fobj:
                sys.stdout.write(fobj.read())
    except IOError as e:
        click.echo("ERROR {}: {}".format(e.errno, str(e)), err=True)
        sys.exit(1)

    try:
        os.remove(f.name)
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
