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
from collections.abc import Callable, Mapping

from typing_extensions import is_typeddict

from aiida.common.exceptions import GraphError, GraphTypeCheckError, GraphValidationError
from aiida.common.lang import override
from aiida.engine.processes.functions import (
    FunctionProcessBase,
    P,
    ProcessFunctionType,
    declare_output_ports,
    process_function,
)
from aiida.engine.processes.generic.ports import UNSPECIFIED
from aiida.engine.processes.graphs.ir import TaskIR, fixed_inputs
from aiida.engine.processes.port_model import field_from_annotation, is_structured
from aiida.engine.processes.ports import PortNamespace
from aiida.engine.processes.process_spec import GraphProcessSpec, ProcessSpec
from aiida.orm import CalcFunctionNode, Data, to_aiida_type

__all__ = ('TaskHandle', 'TaskProcess')

R = t.TypeVar('R')


class TaskProcess(FunctionProcessBase):  # NOTE: converge with FunctionProcess, or keep both leaves (to be decided).
    """Task process with plain Python inputs and static leaf outputs."""

    _spec_class = GraphProcessSpec
    # Set at declaration: a total `TypedDict` return declares one port per key.
    _named_outputs: t.ClassVar[bool] = False

    @classmethod
    @override
    def _declare_input(
        cls,
        spec: ProcessSpec,
        parameter: inspect.Parameter,
        annotations: dict[str, t.Any],
        param_help_string: dict[str, str | None],
    ) -> None:
        if not isinstance(spec, GraphProcessSpec):
            msg = f'task inputs need a graph spec, not `{type(spec).__name__}`.'
            raise TypeError(msg)
        spec.input_from_field(
            parameter.name,
            field_from_annotation(
                parameter.name,
                annotations.get(parameter.name),
                parameter.default if parameter.default is not parameter.empty else UNSPECIFIED,
                param_help_string.get(parameter.name),
            ),
        )

    @classmethod
    @override
    def _declare_outputs(cls, spec: ProcessSpec, annotations: dict[str, t.Any]) -> None:
        declare_output_ports(annotations.get('return'), spec)
        spec.outputs.dynamic = False
        cls._named_outputs = is_typeddict(annotations.get('return'))

    @override
    def _out_result(self, result: t.Any) -> None:
        outputs = self.spec().outputs
        names = list(outputs)
        if self._named_outputs and not isinstance(result, Mapping):
            msg = f'task declares named outputs {names} but returned a single value; return a mapping instead.'
            raise GraphValidationError(msg)
        if isinstance(result, Mapping) and self._named_outputs:
            missing = [name for name in names if name not in result]
            if missing:
                msg = f'task omitted declared outputs {missing}; return every declared output.'
                raise GraphValidationError(msg)
            values = tuple(result[name] for name in names)
        else:
            values = result if isinstance(result, tuple) else (result,)
        if not names and result is None:
            return
        if len(values) != len(names):
            msg = f'task declares {len(names)} outputs {names} but returned {len(values)} values.'
            raise GraphValidationError(msg)
        stored = {
            name: value if isinstance(value, Data) else to_aiida_type(value)
            for name, value in zip(names, values, strict=True)
        }
        super()._out_result(stored)


class TaskHandle(t.Generic[P, R]):
    """A callable process function carrying its graph declaration."""

    is_process_function = True

    def __init__(self, function: ProcessFunctionType[P, R, CalcFunctionNode]) -> None:
        self._function = function
        self._task_spec = TaskIR.from_process(function)
        # Copy name and docstring, not the function state: the handle owns its task spec.
        functools.update_wrapper(self, function, updated=())

    @t.overload
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

    @t.overload
    def __call__(self: TaskHandle[P, R], *args: t.Any, after: t.Any = ..., **kwargs: t.Any) -> R: ...

    def __call__(self, *args: t.Any, after: t.Any = None, **kwargs: t.Any) -> t.Any:
        if after is not None:
            msg = '`after` orders placements in a `@graph` body; it is not a task input.'
            raise GraphError(msg)
        return self._function(*args, **kwargs)

    @property
    def process_class(self) -> type[TaskProcess]:
        """Return the task process class behind the decorated function."""
        # `build_task` always decorates with `TaskProcess` as the base class.
        return t.cast(type[TaskProcess], self._function.process_class)

    @property
    def node_class(self) -> type[CalcFunctionNode]:
        """Return the provenance node class of task runs."""
        return CalcFunctionNode

    def get_launch_inputs(self, **inputs: t.Any) -> dict[str, t.Any]:
        """Validate the task inputs through the decorated function."""
        return self._function.get_launch_inputs(**inputs)

    def spec(self) -> ProcessSpec:
        """Return the process spec of the task process class."""
        return self.process_class.spec()

    def run(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Run the task function locally and return its outputs."""
        return self._function.run(*args, **kwargs)

    def run_get_node(self, *args: P.args, **kwargs: P.kwargs) -> tuple[dict[str, t.Any] | None, CalcFunctionNode]:
        """Run the task function locally and return its outputs with the node."""
        return self._function.run_get_node(*args, **kwargs)

    def run_get_pk(self, *args: P.args, **kwargs: P.kwargs) -> tuple[dict[str, t.Any] | None, int]:
        """Run the task function locally and return its outputs with the node pk."""
        return self._function.run_get_pk(*args, **kwargs)

    def recreate_from(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        """Recreate the task node from cached inputs through the decorated function."""
        return self._function.recreate_from(*args, **kwargs)


def _check_task_contract(function: Callable[..., t.Any]) -> None:  # NOTE: strict annotation resolution for tasks?
    """Reject task declarations the graph runtime cannot represent."""
    signature = inspect.signature(function)
    if 'after' in signature.parameters:
        msg = '`after` is reserved for source graph ordering dependencies.'
        raise GraphError(msg)
    hints = t.get_type_hints(function, include_extras=True)
    annotation = hints.get('return', inspect.Signature.empty)
    if is_structured(annotation):
        msg = 'task output namespaces are not supported; declare leaf outputs instead.'
        raise GraphTypeCheckError(msg)
    if annotation is inspect.Signature.empty:
        msg = (
            'tasks require a return annotation to wire their outputs; '
            'annotate the function or wrap third-party functions in an annotated one.'
        )
        raise GraphTypeCheckError(msg)


def build_task(function: Callable[P, R]) -> TaskHandle[P, R]:
    """Construct a task process with static leaf outputs and Python-valued inputs."""
    _check_task_contract(function)
    decorated = process_function(node_class=CalcFunctionNode, base_class=TaskProcess)(function)
    handle = TaskHandle(t.cast(ProcessFunctionType[P, R, CalcFunctionNode], decorated))
    spec = handle.process_class.spec()
    fixed_inputs(spec.inputs)
    if any(isinstance(port, PortNamespace) for port in spec.outputs.values()):
        msg = 'tasks require static leaf outputs; declare leaf outputs instead.'
        raise GraphTypeCheckError(msg)
    return handle
