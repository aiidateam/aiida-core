# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Convenience functions to add awaitables to the Context of a WorkChain."""
from __future__ import annotations

from aiida.orm import ProcessNode

from .awaitable import SubProcessRef, construct_sub_ref

__all__ = ('ToContext', 'assign_', 'append_')

ToContext = dict


def assign_(target: ProcessNode) -> SubProcessRef:
    """Construct a pointer for a given sub-process of a workchain step.

    When the sub-process is completed,
    it will be assigned to a key within the context (the key is defined later).
    """
    process_ref = construct_sub_ref(target)
    process_ref.action = 'assign'
    return process_ref


def append_(target: ProcessNode) -> SubProcessRef:
    """Construct a pointer for a given sub-process of a workchain step.

    When the sub-process is completed,
    it will be appended to a list that is assigned toa  key within the context  (the key is defined later).
    """
    process_ref = construct_sub_ref(target)
    process_ref.action = 'append'
    return process_ref
