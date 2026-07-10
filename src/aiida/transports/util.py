###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""General utilities for Transport classes."""

from aiida.common.extendeddicts import FixedFieldsAttributeDict


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


async def copy_from_remote_to_remote_async(
    transportsource, transportdestination, remotesource, remotedestination, **kwargs
):
    """Copy files or folders from a remote computer to another remote computer.
    Note: To have a proper async performance,
    both transports should be instance `core.async_ssh`.
    Even if either or both are not async, the function will work,
    but the performance might be lower than the sync version.

    :param transportsource: transport to be used for the source computer
    :param transportdestination: transport to be used for the destination computer
    :param str remotesource: path to the remote source directory / file
    :param str remotedestination: path to the remote destination directory / file
    :param kwargs: keyword parameters passed to the final put,
        except for 'dereference' that is passed to the initial get

    .. note:: it uses the method transportsource.copy_from_remote_to_remote
    """
    await transportsource.copy_from_remote_to_remote(transportdestination, remotesource, remotedestination, **kwargs)
