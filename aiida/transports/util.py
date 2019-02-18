# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""General utilities for Transport classes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import time

from paramiko import ProxyCommand
from six.moves import range

from aiida.common.extendeddicts import FixedFieldsAttributeDict


class FileAttribute(FixedFieldsAttributeDict):
    """
    A class, resembling a dictionary, to describe the attributes of a file,
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

    def __init__(self, command_line):  # pylint: disable=super-init-not-called
        # Note that the super().__init__ MUST NOT be called here, otherwise
        # two subprocesses will be created.
        import os
        from subprocess import Popen, PIPE
        from shlex import split as shlsplit

        self.cmd = shlsplit(command_line)
        self.process = Popen(self.cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=0, preexec_fn=os.setsid)  # pylint: disable=subprocess-popen-preexec-fn
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


def copy_from_remote_to_remote(transportsource, transportdestination, remotesource, remotedestination, **kwargs):
    """
    Copy files or folders from a remote computer to another remote computer.

    :param transportsource: transport to be used for the source computer
    :param transportdestination: transport to be used for the destination computer
    :param str remotesource: path to the remote source directory / file
    :param str remotedestination: path to the remote destination directory / file
    :param kwargs: keyword parameters passed to the final put,
        except for 'dereference' that is passed to the initial get

    .. note:: it uses the method transportsource.copy_from_remote_to_remote
    """
    transportsource.copy_from_remote_to_remote(transportdestination, remotesource, remotedestination, **kwargs)
