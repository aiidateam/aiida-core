###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Resolve source call bindings independently of syntax lowering and task registration."""

from collections.abc import Callable

from aiida.engine.processes.graphs.spec import TaskSpec


def resolve_binding(function: Callable, name: str) -> object:
    """Resolve a name in the defining function's globals, including imported aliases.

    Bindings are read at build time so declarations may refer to definitions later in
    the module. No callable is invoked and no callee source is inspected.
    """
    return function.__globals__.get(name)


def task_spec_for(target: object) -> TaskSpec | None:
    """Return a bound task declaration without depending on how it was registered."""
    spec = getattr(target, 'task_spec', None)
    return spec if isinstance(spec, TaskSpec) else None
