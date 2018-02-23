# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import aiida.common
from aiida.common.exceptions import InternalError
from aiida.common.extendeddicts import FixedFieldsAttributeDict

from aiida.transport.transport import Transport
from aiida.transport.util import TransportFactory


def copy_from_remote_to_remote(transportsource, transportdestination,
                               remotesource, remotedestination, **kwargs):
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
    transportsource.copy_from_remote_to_remote(
        transportdestination, remotesource, remotedestination, **kwargs)
