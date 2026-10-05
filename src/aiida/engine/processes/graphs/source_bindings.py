###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Resolve source callees without invoking them or registering process aliases."""

from __future__ import annotations

import typing as t
from collections.abc import Callable

from aiida.engine.processes.graphs.spec import TaskSpec
from aiida.engine.processes.graphs.tasks import TaskHandle


def resolve_binding(function: Callable[..., t.Any], name: str) -> object:
    return function.__globals__.get(name)


def task_spec_for(target: object) -> TaskSpec | None:
    return target.task_spec if isinstance(target, TaskHandle) else None
