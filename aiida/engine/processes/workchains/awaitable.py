# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Enums and function for the awaitables of Processes."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from aiida.orm import ProcessNode


@dataclass
class SubProcessRef:
    """A pointer to a sub-process, for a workchain step to await on."""
    pk: int
    """The pk of the sub-process."""
    action: Literal['assign', 'append'] = 'assign'
    """How to store the result in the workchain context; either assigning directly to a key or appending to a list."""
    outputs: bool = False
    """Whether the node itself (False) or its outputs (True) should be added to the context."""
    key: None | str = None
    """The key to store the result under in the workchain context."""
    resolved: bool = False
    """Whether the process has been resolved and the result is available on the context."""


def construct_sub_ref(target: ProcessNode | SubProcessRef) -> SubProcessRef:
    """Construct a pointer for a given sub-process of a workchain step."""
    if isinstance(target, SubProcessRef):
        return target
    if isinstance(target, ProcessNode):
        return SubProcessRef(pk=target.pk)

    raise ValueError(f'invalid class for sub-process: {type(target)}')


# NOTE: the following classes are only here for back-compatibility,
# if a profile still has a workchain context with the old format of awaitable stored in it.


class AwaitableTarget(Enum):
    """Enum that describes the class of the target a given awaitable."""
    PROCESS = 'process'


class AwaitableAction(Enum):
    """Enum that describes the action to be taken for a given awaitable."""
    ASSIGN = 'assign'
    APPEND = 'append'
