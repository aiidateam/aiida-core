###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data core.remote` command."""

import stat
from pathlib import Path

import click

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.params import arguments, types
from aiida.cmdline.utils import echo


@verdi_data.group('core.remote')
def remote():
    """Manipulate RemoteData objects (reference to remote folders).

    A RemoteData can be thought as a "symbolic link" to a folder on one of the
    Computers set up in AiiDA (e.g. where a CalcJob will run).
    This folder is called "remote" in the sense that it is on a Computer and
    not in the AiiDA repository. Note, however, that the "remote" computer
    could also be "localhost".
    """


@remote.command('ls')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:core.remote',)))
@click.option('-l', '--long', 'ls_long', is_flag=True, default=False, help='Display also file metadata.')
@click.option('-p', '--path', type=click.STRING, default='.', help='The folder to list.')
def remote_ls(ls_long, path, datum):
    """List content of a (sub)directory in a RemoteData object."""
    import datetime

    try:
        content = datum.listdir_withattributes(path=path)
    except OSError as err:
        echo.echo_critical(f'Unable to access the remote folder or file, check if it exists.\nOriginal error: {err!s}')
    for metadata in content:
        if ls_long:
            mtime = datetime.datetime.fromtimestamp(metadata['attributes'].st_mtime)
            pre_line = '{} {:10}  {}  '.format(
                stat.filemode(metadata['attributes'].st_mode),
                metadata['attributes'].st_size,
                mtime.strftime('%d %b %Y %H:%M'),
            )
            echo.echo(pre_line, nl=False)
        if metadata['isdir']:
            echo.echo(metadata['name'], fg=echo.COLORS['info'])
        else:
            echo.echo(metadata['name'])


@remote.command('cat')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:core.remote',)))
@click.argument('path', type=click.STRING)
def remote_cat(datum, path):
    """Show content of a file in a RemoteData object."""
    import os
    import sys
    import tempfile

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmpf:
            tmpf.close()
            datum.getfile(path, tmpf.name)
            with open(tmpf.name, encoding='utf8') as fhandle:
                sys.stdout.write(fhandle.read())
    except OSError as err:
        echo.echo_critical(f'{err.errno}: {err!s}')

    try:
        os.remove(tmpf.name)
    except OSError:
        # If you cannot delete, ignore (maybe I didn't manage to create it in the first place
        pass


@remote.command('show')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:core.remote',)))
def remote_show(datum):
    """Show information for a RemoteData object."""
    echo.echo(f'- Remote computer name: {datum.computer.label}')
    echo.echo(f'- Remote folder full path: {datum.get_remote_path()}')


@remote.command('size')
@arguments.NODE()
@click.option(
    '-m',
    '--method',
    type=click.STRING,
    default='du',
    help='The method that should be used to evaluate the size (either ``du`` or ``stat``.)',
)
@click.option(
    '-p',
    '--path',
    type=click.Path(),
    default=None,
    help='Relative path of the object of the ``RemoteData`` node for which the size should be evaluated.',
)
@click.option(
    '-b',
    '--bytes',
    'return_bytes',
    type=bool,
    is_flag=True,
    default=False,
    help='Return the size in bytes or human-readable format?',
)
def remote_size(node, method, path, return_bytes):
    """Obtain the total size of a file or directory at a given path that is stored via a ``RemoteData`` object."""
    try:
        # `method` might change, if `du` fails, so assigning to new variable here
        total_size, used_method = node.get_size_on_disk(relpath=path, method=method, return_bytes=return_bytes)
        remote_path = Path(node.get_remote_path())
        full_path = remote_path / path if path is not None else remote_path
        echo.echo_success(
            f'Estimated total size of path `{full_path}` on the Computer '
            f'<{node.computer.label}> obtained via `{used_method}`: {total_size}'
        )
    except (OSError, FileNotFoundError, NotImplementedError) as exc:
        echo.echo_critical(str(exc))
