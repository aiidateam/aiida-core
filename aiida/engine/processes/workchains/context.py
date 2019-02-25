# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Convenience functions to add awaitables to the Context of a WorkChain."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .awaitable import construct_awaitable, AwaitableAction

__all__ = ('ToContext', 'assign_', 'append_')

ToContext = dict


def assign_(target):
    """
    Convenience function that will construct an Awaitable for a given class instance
    with the context action set to ASSIGN. When the awaitable target is completed
    it will be assigned to the context for a key that is to be defined later

    :param target: an instance of a Process or Awaitable
    :returns: the awaitable
    :rtype: Awaitable
    """
    awaitable = construct_awaitable(target)
    awaitable.action = AwaitableAction.ASSIGN
    return awaitable


def append_(target):
    """
    Convenience function that will construct an Awaitable for a given class instance
    with the context action set to APPEND. When the awaitable target is completed
    it will be appended to a list in the context for a key that is to be defined later

    :param target: an instance of a Process or Awaitable
    :returns: the awaitable
    :rtype: Awaitable
    """
    awaitable = construct_awaitable(target)
    awaitable.action = AwaitableAction.APPEND
    return awaitable
