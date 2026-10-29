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
from aiida.engine.processes.calcjobs import CalcJob
from aiida.engine.processes.functions import FunctionProcessBase, P, ProcessFunctionType, process_function
from aiida.engine.processes.generic.ports import UNSPECIFIED
from aiida.engine.processes.graphs.ir import TaskIR, reject_dynamic_inputs
from aiida.engine.processes.port_model import _without_marks, field_from_annotation, is_structured
from aiida.engine.processes.ports import PortNamespace, _infer_node_types
from aiida.engine.processes.process import Process
from aiida.engine.processes.process_spec import GraphProcessSpec, ProcessSpec
from aiida.engine.processes.workchains.workchain import WorkChain
from aiida.orm import CalcFunctionNode, CalcJobNode, Data, WorkChainNode, to_aiida_type

__all__ = (
    'CalcJobTaskHandle',
    'FunctionTaskHandle',
    'TaskProcess',
    'WorkChainTaskHandle',
)


R = t.TypeVar('R')


def _declare_output_ports(return_annotation: t.Any, spec: ProcessSpec) -> None:
    """Declare static leaf output ports from the return annotation.

    A scalar annotation declares one ``result`` port; a total ``TypedDict`` declares one
    port per key. Task registration rejects missing declarations and namespace returns.

    :param return_annotation: the return annotation of the wrapped function, if it has one.
    :param spec: the spec to declare them on.
    """
    if return_annotation is None or return_annotation is type(None):
        return
    if is_typeddict(return_annotation):
        hints = t.get_type_hints(return_annotation, include_extras=True)
        if set(hints) != set(return_annotation.__required_keys__):
            msg = 'TypedDict task outputs must be total; declare every output.'
            raise GraphTypeCheckError(msg)
        for key, hint in hints.items():
            spec.output(key, valid_type=_infer_node_types(_without_marks(hint)) or (Data,))
        return
    if t.get_origin(return_annotation) is tuple:
        msg = 'name multiple task outputs with a TypedDict instead of a tuple.'
        raise GraphTypeCheckError(msg)
    if t.get_origin(return_annotation) in (list, dict):
        origin = t.get_origin(return_annotation)
    else:
        origin = return_annotation
    spec.output(
        Process.SINGLE_OUTPUT_LINKNAME,
        valid_type=_infer_node_types(origin) or (Data,),
    )


class TaskProcess(FunctionProcessBase):
    """Task process with plain Python inputs and static leaf outputs."""

    _allow_persistence = True
    """Task children checkpoint on daemon workers; the generated class travels as bytes."""

    _spec_class: type[GraphProcessSpec] = GraphProcessSpec
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
        _declare_output_ports(annotations.get('return'), spec)
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
            extra = [name for name in result if name not in names]
            if extra:
                msg = f'task returned undeclared outputs {extra}; return only declared outputs.'
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


class FunctionTaskHandle(t.Generic[P, R]):
    """A callable process function carrying its graph declaration."""

    is_process_function: t.ClassVar[bool] = True

    def __init__(self, function: ProcessFunctionType[P, R, CalcFunctionNode]) -> None:
        self._function: ProcessFunctionType[P, R, CalcFunctionNode] = function
        self._task_spec: TaskIR = TaskIR.from_process(function)
        # Copy name and docstring, not the function state: the handle owns its task spec.
        functools.update_wrapper(self, function, updated=())

    @t.overload
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

    @t.overload
    def __call__(self: FunctionTaskHandle[P, R], *args: t.Any, after: t.Any = ..., **kwargs: t.Any) -> R: ...

    def __call__(self, *args: t.Any, after: t.Any = None, **kwargs: t.Any) -> t.Any:
        """Run the task function and return its result."""
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


class CalcJobTaskHandle:
    """A `CalcJob` subclass carrying its graph declaration, launched with per-placement metadata."""

    is_process_function: t.ClassVar[bool] = False

    def __init__(self, process_class: type[CalcJob]) -> None:
        self._process_class: type[CalcJob] = process_class
        self._task_spec: TaskIR = TaskIR.from_process(process_class)
        # Copy name and docstring, not the class state: the handle owns its task spec.
        functools.update_wrapper(self, process_class, updated=())

    def __call__(self, *args: t.Any, after: t.Any = None, **kwargs: t.Any) -> t.Any:
        """Execute the task and return its node."""
        if after is not None:
            msg = '`after` orders placements in a `@graph` body; it is not a task input.'
            raise GraphError(msg)
        if args:
            msg = 'CalcJob tasks take named inputs only; pass each input by name instead.'
            raise GraphError(msg)
        from aiida.engine.launch import run_get_node

        _, node = run_get_node(self._process_class, **kwargs)
        return node

    @property
    def process_class(self) -> type[CalcJob]:
        """Return the task process class behind the handle."""
        return self._process_class

    @property
    def node_class(self) -> type[CalcJobNode]:
        """Return the provenance node class of task runs."""
        return CalcJobNode

    def get_launch_inputs(self, **inputs: t.Any) -> dict[str, t.Any]:
        """Return the task inputs; the process prepares and validates them against its spec."""
        return dict(inputs)

    def spec(self) -> ProcessSpec:
        """Return the process spec of the task process class."""
        return self._process_class.spec()


class WorkChainTaskHandle:
    """A `WorkChain` subclass carrying its graph declaration, wired on graph inputs only."""

    is_process_function: t.ClassVar[bool] = False

    def __init__(self, process_class: type[WorkChain]) -> None:
        self._process_class: type[WorkChain] = process_class
        self._task_spec: TaskIR = TaskIR.from_process(process_class)
        # Copy name and docstring, not the class state: the handle owns its task spec.
        functools.update_wrapper(self, process_class, updated=())

    def __call__(self, *args: t.Any, after: t.Any = None, **kwargs: t.Any) -> t.Any:
        """Execute the task and return its node."""
        if after is not None:
            msg = '`after` orders placements in a `@graph` body; it is not a task input.'
            raise GraphError(msg)
        if args:
            msg = 'WorkChain tasks take named inputs only; pass each input by name instead.'
            raise GraphError(msg)
        from aiida.engine.launch import run_get_node

        _, node = run_get_node(self._process_class, **kwargs)
        return node

    @property
    def process_class(self) -> type[WorkChain]:
        """Return the task process class behind the handle."""
        return self._process_class

    @property
    def node_class(self) -> type[WorkChainNode]:
        """Return the provenance node class of task runs."""
        return WorkChainNode

    def get_launch_inputs(self, **inputs: t.Any) -> dict[str, t.Any]:
        """Return the task inputs; the process prepares and validates them against its spec."""
        return dict(inputs)

    def spec(self) -> ProcessSpec:
        """Return the process spec of the task process class."""
        return self._process_class.spec()


def _needs_metadata(task: t.Any) -> bool:
    """Return whether a placement dispatches a `CalcJob` directly."""
    from aiida.engine.processes.graphs.ir import ProcessTask

    if not isinstance(task, ProcessTask):
        return False
    return issubclass(task.spec.process_class, CalcJob)


def _launch_inputs(task: t.Any, provided: Mapping[str, t.Any], inputs: dict[str, t.Any]) -> dict[str, t.Any]:
    """Merge the stashed per-placement `CalcJob` metadata, failing loudly when absent."""
    from aiida.engine.processes.graphs.ir import ProcessTask

    assert isinstance(task, ProcessTask)
    placement = task.name
    try:
        metadata = provided[placement]
    except KeyError:
        msg = (
            f'task `{placement}` is a `CalcJob` and needs launch metadata; '
            f"pass it keyed by placement name, e.g. `metadata={{'{placement}': {{...}}}}`."
        )
        raise GraphValidationError(msg) from None
    if not isinstance(metadata, Mapping):
        msg = f'task `{placement}` metadata must be a mapping of metadata inputs, not `{type(metadata)}`.'
        raise GraphValidationError(msg)
    return {**inputs, 'metadata': {**dict(metadata), **inputs.get('metadata', {})}}


def _check_task_contract(
    function: type[CalcJob] | type[WorkChain] | Callable[..., t.Any],
) -> None:
    """Reject task declarations the graph runtime cannot represent."""
    if inspect.isclass(function) and issubclass(function, (CalcJob, WorkChain)):
        spec = function.spec()
        reject_dynamic_inputs(spec.inputs)
        if spec.outputs.dynamic or any(isinstance(port, PortNamespace) for port in spec.outputs.values()):
            msg = 'tasks require static leaf outputs; declare leaf outputs instead.'
            raise GraphTypeCheckError(msg)
        return
    if inspect.isclass(function):
        msg = 'tasks accept functions, a `CalcJob` subclass, or a `WorkChain` subclass; not other process classes.'
        raise GraphTypeCheckError(msg)
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


def build_task(
    function: type[CalcJob] | type[WorkChain] | Callable[P, R],
) -> CalcJobTaskHandle | WorkChainTaskHandle | FunctionTaskHandle[P, R]:
    """Construct a task handle with static leaf outputs and fixed graph inputs."""
    _check_task_contract(function)
    if inspect.isclass(function) and issubclass(function, CalcJob):
        return CalcJobTaskHandle(function)
    if inspect.isclass(function) and issubclass(function, WorkChain):
        return WorkChainTaskHandle(function)
    assert not inspect.isclass(function)
    decorated = process_function(node_class=CalcFunctionNode, base_class=TaskProcess)(function)
    handle = FunctionTaskHandle(t.cast(ProcessFunctionType[P, R, CalcFunctionNode], decorated))
    spec = handle.process_class.spec()
    reject_dynamic_inputs(spec.inputs)
    if any(isinstance(port, PortNamespace) for port in spec.outputs.values()):
        msg = 'tasks require static leaf outputs; declare leaf outputs instead.'
        raise GraphTypeCheckError(msg)
    return handle
