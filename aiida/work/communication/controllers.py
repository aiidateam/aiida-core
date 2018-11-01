# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement
"""Methods for creating, setting and getting the global process controller."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import plumpy

__all__ = ['create_controller', 'get_controller', 'set_controller']

CONTROLLER = None


def create_controller(communicator=None):
    """
    Create a Controller

    :param communicator: a :class:`~kiwipy.Communicator`
    :return: a :class:`~plumpy.RemoteProcessThreadController` instance
    """
    if communicator is None:
        from aiida.work.communication.communicators import get_communicator
        communicator = get_communicator()

    return plumpy.RemoteProcessThreadController(communicator=communicator)


def get_controller():
    """
    Get the global controller instance

    :returns: the global controller
    """
    global CONTROLLER

    if CONTROLLER is None:
        CONTROLLER = create_controller()

    return CONTROLLER


def set_controller(controller):
    """
    Set the global controller instance

    :param controller: the controller instance to set as the global process controller
    """
    global CONTROLLER
    CONTROLLER = controller
