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
import textwrap
import typing as t
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from aiida.common.exceptions import UnsupportedSyntax
from aiida.common.lang import override
from aiida.engine.processes.functions import FunctionProcess, P, ProcessFunctionType, process_function
from aiida.engine.processes.graphs.spec import TaskSpec, fixed_inputs
from aiida.engine.processes.port_model import is_structured
from aiida.engine.processes.ports import PortNamespace
from aiida.engine.processes.process_spec import ProcessSpec
from aiida.orm import CalcFunctionNode, Data, to_aiida_type

__all__ = ('TaskHandle', 'TaskProcess')

R = t.TypeVar('R')


class TaskProcess(FunctionProcess):
    """Consume declared Python/ORM inputs and create provenance nodes for leaf outputs."""

    NODE_INPUT_TYPES: t.ClassVar[bool] = False

    @override
    def _out_result(self, result: t.Any) -> None:
        outputs = self.spec().outputs
        names = list(outputs)
        values = result if isinstance(result, tuple) else (result,)
        if not names and result is None:
            return
        if len(values) != len(names):
            msg = f'task declares {len(names)} outputs {names} but returned {len(values)} values.'
            raise ValueError(msg)
        stored = {
            name: value if isinstance(value, Data) else to_aiida_type(value)
            for name, value in zip(names, values, strict=True)
        }
        super()._out_result(stored)


def _key(function: Callable[..., t.Any]) -> str:
    """Return the registry key of a declaration, rejecting nested functions."""
    if not inspect.isfunction(function):
        raise UnsupportedSyntax('Registered declarations must be Python functions, not process classes or builders')
    if function.__qualname__ != function.__name__:
        raise UnsupportedSyntax('Registered functions must be defined at module scope, not nested in other code')
    if function.__module__ == '__main__':
        msg = 'Graph declarations require an importable module; save the function in a Python module.'
        raise UnsupportedSyntax(msg)
    return f'{function.__module__}:{function.__name__}'


@dataclass(frozen=True)
class _SourceDefinition:
    """A source decorator's captured definition, owned independently of registry lookups."""

    key: str
    kind: t.Literal['graph', 'task']
    function: Callable[..., t.Any]
    source: str
    filename: str
    first_line: int
    hints: Mapping[str, t.Any]


class _SourceRegistry:
    """Own definitions captured by the graph and task decorators."""

    def __init__(self) -> None:
        self._definitions: dict[str, _SourceDefinition] = {}

    def register(self, function: Callable[..., t.Any], *, kind: t.Literal['graph', 'task']) -> _SourceDefinition:
        """Capture a definition atomically, without executing its body."""
        key = _key(function)
        if key in self._definitions:
            msg = f'Duplicate registered function {key}'
            raise UnsupportedSyntax(msg)
        try:
            lines, first_line = inspect.getsourcelines(function)
        except OSError as exception:
            msg = f'Cannot read the source of {key}: definitions need retrievable source.'
            raise UnsupportedSyntax(msg) from exception
        definition = _SourceDefinition(
            key=key,
            kind=kind,
            function=function,
            source=textwrap.dedent(''.join(lines)),
            filename=inspect.getsourcefile(function) or '<unknown>',
            first_line=first_line,
            hints=MappingProxyType(t.get_type_hints(function, include_extras=True)),
        )
        self._definitions[key] = definition
        return definition

    def get_graph(self, key: str) -> _SourceDefinition:
        """Retrieve a source graph once, at the entry to its lowering pipeline."""
        definition = self._definitions.get(key)
        if definition is None or definition.kind != 'graph':
            msg = f'Graph {key} is not registered'
            raise UnsupportedSyntax(msg)
        return definition


_SOURCE_REGISTRY = _SourceRegistry()
"""The single registry owning live source definitions."""


class TaskHandle(t.Generic[P, R]):
    """A callable process function carrying its graph declaration."""

    is_process_function = True

    def __init__(self, function: ProcessFunctionType[P, R, CalcFunctionNode]) -> None:
        self._function = function
        self.task_spec = TaskSpec.from_process(function)
        functools.update_wrapper(self, function, updated=())

    @t.overload
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

    @t.overload
    def __call__(self: TaskHandle[P, R], *args: t.Any, after: t.Any = ..., **kwargs: t.Any) -> R: ...

    def __call__(self, *args: t.Any, after: t.Any = None, **kwargs: t.Any) -> t.Any:
        if after is not None:
            msg = '`after` orders placements in a `@graph` body; it is not a task input.'
            raise TypeError(msg)
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


def _check_task_contract(function: Callable[..., t.Any], outputs: Sequence[str] | None) -> Sequence[str] | None:
    """Reject task declarations the graph runtime cannot represent."""
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
    return outputs


def build_task(function: Callable[P, R], *, outputs: Sequence[str] | None = None) -> TaskHandle[P, R]:
    """Construct a task process with static leaf outputs and Python-valued inputs."""
    outputs = _check_task_contract(function, outputs)
    decorated = process_function(node_class=CalcFunctionNode, base_class=TaskProcess, outputs=outputs)(function)
    handle = TaskHandle(t.cast(ProcessFunctionType[P, R, CalcFunctionNode], decorated))
    spec = handle.process_class.spec()
    fixed_inputs(spec.inputs)
    if spec.outputs.dynamic or any(isinstance(port, PortNamespace) for port in spec.outputs.values()):
        msg = 'tasks require static leaf outputs.'
        raise TypeError(msg)
    return handle
