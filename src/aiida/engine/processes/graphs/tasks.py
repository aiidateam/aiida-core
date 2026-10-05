###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Task construction shared by source declarations and their process runtime."""

from __future__ import annotations

import functools
import inspect
import typing as t
from collections.abc import Callable, Sequence

from aiida.engine.processes.functions import process_function
from aiida.engine.processes.graphs.process import TaskProcess
from aiida.engine.processes.graphs.spec import TaskSpec, fixed_inputs
from aiida.engine.processes.port_model import is_structured
from aiida.engine.processes.ports import PortNamespace
from aiida.orm import CalcFunctionNode

__all__ = ('TaskHandle',)


class TaskHandle:
    """A callable process function carrying its graph declaration."""

    is_process_function = True

    def __init__(self, function: t.Any) -> None:
        self._function = function
        self.task_spec = TaskSpec.from_process(function)
        functools.update_wrapper(self, function, updated=())

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self._function(*args, **kwargs)

    @property
    def process_class(self) -> type[TaskProcess]:
        return self._function.process_class

    @property
    def node_class(self) -> type[CalcFunctionNode]:
        return CalcFunctionNode

    def get_launch_inputs(self, **inputs: t.Any) -> dict[str, t.Any]:
        return self._function.get_launch_inputs(**inputs)

    def spec(self) -> t.Any:
        return self.process_class.spec()

    def run(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self._function.run(*args, **kwargs)

    def run_get_node(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self._function.run_get_node(*args, **kwargs)

    def run_get_pk(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self._function.run_get_pk(*args, **kwargs)

    def recreate_from(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self._function.recreate_from(*args, **kwargs)


def build_task(function: Callable[..., t.Any], *, outputs: Sequence[str] | None = None) -> TaskHandle:
    """Construct a task process with static leaf outputs and Python-valued inputs."""
    signature = inspect.signature(function)
    if 'after' in signature.parameters:
        msg = '`after` is reserved for source graph ordering dependencies.'
        raise TypeError(msg)
    hints = t.get_type_hints(function, include_extras=True)
    annotation = hints.get('return', inspect.Signature.empty)
    if is_structured(annotation):
        msg = 'task output namespaces are not supported; declare leaf outputs instead.'
        raise TypeError(msg)
    if outputs is None:
        if annotation is inspect.Signature.empty:
            msg = 'tasks require a return annotation or explicit static output names.'
            raise TypeError(msg)
        if annotation is type(None):
            outputs = ()
    if outputs is not None:
        if (
            isinstance(outputs, str)
            or any(not name.isidentifier() for name in outputs)
            or len(set(outputs)) != len(outputs)
        ):
            msg = 'task outputs must be unique identifier names.'
            raise TypeError(msg)
    decorated = process_function(node_class=CalcFunctionNode, base_class=TaskProcess, outputs=outputs)(function)
    handle = TaskHandle(decorated)
    spec = handle.process_class.spec()
    fixed_inputs(spec.inputs)
    if spec.outputs.dynamic or any(isinstance(port, PortNamespace) for port in spec.outputs.values()):
        msg = 'tasks require static leaf outputs.'
        raise TypeError(msg)
    return handle
