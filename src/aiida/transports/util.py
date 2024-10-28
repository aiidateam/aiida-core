###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""General utilities for Transport classes."""

import time
from pathlib import Path, PurePosixPath
from typing import Union

from paramiko import ProxyCommand

from aiida.common.extendeddicts import FixedFieldsAttributeDict


class StrPath:
    """A class to chain paths together.
    This is useful to avoid the need to use os.path.join to chain paths.

    Note:
    Eventually transport plugins may further develope so that functions with pathlib.Path
    So far they are expected to work only with POSIX paths.
    This class is a solution to avoid the need to use Path.join to chain paths and convert back again to str.
    """

    def __init__(self, path: Union[str, PurePosixPath]):
        """Chain a path with multiple paths.

        :param path: the initial path (absolute)
        """
        if isinstance(path, PurePosixPath):
            path = str(path)
        self.str = path.rstrip('/')

    def join(self, *paths: Union[str, PurePosixPath, Path], return_str=True) -> Union[str, 'StrPath']:
        """Join the initial path with multiple paths.

        :param paths: the paths to chain (relative to the previous path)
        :type paths: str or PurePosixPath or Path
        :param return_str: if True, return a string, otherwise return a new StrPath object

        :return: a new StrPath object
        """
        path = self.str
        for p in paths:
            p_ = str(p) if isinstance(p, (PurePosixPath, Path)) else p
            if self.str in p_:
                raise ValueError(
                    'The path to join is already included in the initial path, '
                    'probably you are trying to join an absolute path'
                )
            path = f"{path}/{p_.strip('/')}"

        if return_str:
            return path

        return StrPath(path)


class FileAttribute(FixedFieldsAttributeDict):
    """A class, resembling a dictionary, to describe the attributes of a file,
    that is returned by get_attribute().
    Possible keys: st_size, st_uid, st_gid, st_mode, st_atime, st_mtime
    """

    _valid_fields = (
        'st_size',
        'st_uid',
        'st_gid',
        'st_mode',
        'st_atime',
        'st_mtime',
    )


class _DetachedProxyCommand(ProxyCommand):
    """Modifies paramiko's ProxyCommand by launching the process in a separate process group."""

    def __init__(self, command_line):
        # Note that the super().__init__ MUST NOT be called here, otherwise two subprocesses will be created.
        from shlex import split as shlsplit
        from subprocess import PIPE, Popen

        self.cmd = shlsplit(command_line)
        self.process = Popen(self.cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=0, start_new_session=True)
        self.timeout = None

    def close(self):
        try:
            self.process.terminate()
        # In case the process doesn't exist anymore
        except OSError:
            pass
        for _ in range(10):
            if self.process.poll() is not None:
                break
            time.sleep(0.2)
        else:
            try:
                self.process.kill()
            # In case the process doesn't exist anymore
            except OSError:
                pass
            for _ in range(10):
                if self.process.poll() is not None:
                    break
                time.sleep(0.2)

        for f in [self.process.stdout, self.process.stderr, self.process.stdin]:
            if f is None:
                continue
            try:
                f.close()
            except ValueError:
                pass


def copy_from_remote_to_remote(transportsource, transportdestination, remotesource, remotedestination, **kwargs):
    """Copy files or folders from a remote computer to another remote computer.

    :param transportsource: transport to be used for the source computer
    :param transportdestination: transport to be used for the destination computer
    :param str remotesource: path to the remote source directory / file
    :param str remotedestination: path to the remote destination directory / file
    :param kwargs: keyword parameters passed to the final put,
        except for 'dereference' that is passed to the initial get

    .. note:: it uses the method transportsource.copy_from_remote_to_remote
    """
    transportsource.copy_from_remote_to_remote(transportdestination, remotesource, remotedestination, **kwargs)
