# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-few-public-methods
"""Enums and function for the awaitables of Processes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from enum import Enum

from plumpy.utils import AttributesDict
from aiida.orm import ProcessNode

__all__ = ('Awaitable', 'AwaitableTarget', 'AwaitableAction', 'construct_awaitable')


class Awaitable(AttributesDict):
    """An attribute dictionary that represents an action that a Process could be waiting for to finish."""


class AwaitableTarget(Enum):
    """Enum that describes the class of the target a given awaitable."""
    PROCESS = 'process'


class AwaitableAction(Enum):
    """Enum that describes the action to be taken for a given awaitable."""
    ASSIGN = 'assign'
    APPEND = 'append'


def construct_awaitable(target):
    """
    Construct an instance of the Awaitable class that will contain the information
    related to the action to be taken with respect to the context once the awaitable
    object is completed.

    The awaitable is a simple dictionary with the following keys

        * pk: the pk of the node that is being waited on
        * action: the context action to be performed upon completion
        * outputs: a boolean that toggles whether the node itself

    Currently the only awaitable classes are ProcessNode and Workflow
    The only awaitable actions are the Assign and Append operators
    """
    if isinstance(target, Awaitable):
        return target

    if isinstance(target, ProcessNode):
        awaitable_target = AwaitableTarget.PROCESS
    else:
        raise ValueError('invalid class for awaitable target: {}'.format(type(target)))

    awaitable = Awaitable(**{
        'pk': target.pk,
        'action': AwaitableAction.ASSIGN,
        'target': awaitable_target,
        'outputs': False,
    })

    return awaitable
