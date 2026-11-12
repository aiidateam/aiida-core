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
from aiida.common.links import validate_link_label
from aiida.engine.processes.calcjobs import CalcJob
from aiida.engine.processes.functions import FunctionProcessBase, P, ProcessFunctionType, process_function
from aiida.engine.processes.generic.ports import UNSPECIFIED
from aiida.engine.processes.graphs.ir import TaskIR, TypevarPositions, _reject_dynamic_inputs
from aiida.engine.processes.graphs.shapes import (
    LeafShape,
    NamespaceShape,
    _expanded_annotation,
    _forward_marker,
    _is_type_var,
)
from aiida.engine.processes.port_model import _field_from_annotation, _is_structured, _without_marks
from aiida.engine.processes.ports import PortNamespace, _infer_node_types
from aiida.engine.processes.process import Process
from aiida.engine.processes.process_spec import GraphProcessSpec, ProcessSpec
from aiida.engine.processes.workchains.workchain import WorkChain
from aiida.engine.utils import is_process_function
from aiida.orm import CalcFunctionNode, CalcJobNode, Data, WorkChainNode, to_aiida_type

if t.TYPE_CHECKING:
    from aiida.engine.processes.graphs.ir import ProcessTask

__all__ = (
    'CalcJobTaskHandle',
    'FunctionTaskHandle',
    'PortDeclaration',
    'TaskProcess',
    'WorkChainTaskHandle',
)


R = t.TypeVar('R')


def _typevar_solution(
    target: FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle,
) -> tuple[TypevarPositions, t.Any | None]:
    """Return a task handle's type variable map from its declaration."""
    return target._task_spec.typevar_inputs, target._task_spec.typevar_output


def _typevar_positions(function: Callable[..., t.Any]) -> tuple[TypevarPositions, t.Any | None]:
    """Map each bare `TypeVar` to its input ports and output flag."""
    hints = t.get_type_hints(function, include_extras=True)
    inputs: TypevarPositions = {}
    for name, parameter in inspect.signature(function).parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        hint = hints.get(name, parameter.annotation)
        if hint is inspect.Parameter.empty:
            continue
        bare = _without_marks(hint)
        if _is_type_var(bare):
            inputs.setdefault(bare, []).append(name)
    returned = hints.get('return', inspect.Signature.empty)
    output = None
    if returned is not inspect.Signature.empty and _is_type_var(_without_marks(returned)):
        output = _without_marks(returned)
    return inputs, output


PortDeclaration: t.TypeAlias = Mapping[str, 'type[Data] | tuple[type[Data], ...] | PortDeclaration']
"""Names and node types inside dynamic namespaces, nested like the namespaces they fill."""


def _declared_shape(declaration: PortDeclaration | None, *, leaves: bool = False, path: str = '') -> NamespaceShape:
    """Return the static shape a dynamic-namespace declaration fixes, rejecting non-node types."""
    fields: list[tuple[str, LeafShape | NamespaceShape]] = []
    for name, value in (declaration or {}).items():
        location = f'{path}.{name}' if path else name
        if isinstance(value, Mapping):
            if leaves:
                msg = f'declared output `{location}` is a namespace; task outputs are leaves with one node type each.'
                raise GraphTypeCheckError(msg)
            fields.append((name, _declared_shape(value, path=location)))
            continue
        # Callers outside type checking pass arbitrary objects, so check every entry at runtime.
        given: tuple[object, ...] = value if isinstance(value, tuple) else (value,)
        types = tuple(kind for kind in given if inspect.isclass(kind) and issubclass(kind, Data))
        if not types or len(types) != len(given):
            msg = f'declared port `{location}` takes `Data` subclasses, not `{value!r}`.'
            raise GraphTypeCheckError(msg)
        fields.append((name, LeafShape(types=types)))
    return NamespaceShape(fields=tuple(fields))


def _declare_output_ports(return_annotation: t.Any, spec: ProcessSpec) -> None:
    """Declare static leaf output ports from the return annotation.

    A scalar annotation declares one ``result`` port; a total ``TypedDict`` declares one
    port per key. Task registration rejects missing declarations and namespace returns.

    :param return_annotation: the return annotation of the wrapped function, if it has one.
    :param spec: the spec to declare them on.
    """
    if return_annotation is None or return_annotation is type(None):
        return
    if _forward_marker(return_annotation) is not None:
        msg = 'forward declarations mirror inputs for graph inputs; return a task output instead.'
        raise GraphTypeCheckError(msg)
    return_annotation = _expanded_annotation(return_annotation)
    if is_typeddict(return_annotation):
        hints = t.get_type_hints(return_annotation, include_extras=True)
        if set(hints) != set(return_annotation.__required_keys__):
            msg = 'TypedDict task outputs must be total; declare every output.'
            raise GraphTypeCheckError(msg)
        for key, raw in hints.items():
            hint = _expanded_annotation(raw)
            spec.output(key, valid_type=_infer_node_types(hint) or (Data,))
        return
    if t.get_origin(return_annotation) is tuple or return_annotation is tuple:
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
        annotation = _expanded_annotation(annotations.get(parameter.name))
        spec.input_from_field(
            parameter.name,
            _field_from_annotation(
                parameter.name,
                annotation,
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

    def __init__(
        self,
        function: ProcessFunctionType[P, R, CalcFunctionNode],
        *,
        typevar_inputs: TypevarPositions | None = None,
        typevar_output: t.Any | None = None,
    ) -> None:
        self._function: ProcessFunctionType[P, R, CalcFunctionNode] = function
        self._task_spec: TaskIR = TaskIR.from_process(
            function, typevar_inputs=typevar_inputs, typevar_output=typevar_output
        )
        # Copy name and docstring, not the function state: the handle owns its task spec.
        functools.update_wrapper(self, function, updated=())

    @t.overload
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

    @t.overload
    def __call__(self: FunctionTaskHandle[P, R], *args: t.Any, after: t.Any = ..., **kwargs: t.Any) -> R: ...

    def __call__(self, *args: t.Any, after: t.Any = None, **kwargs: t.Any) -> t.Any:
        """Reject direct calls; tasks run as `@graph` placements or through `run` and `run_get_node`."""
        if after is not None:
            msg = '`after` orders placements in a `@graph` body; it is not a task input.'
            raise GraphError(msg)
        name = getattr(self._function, '__name__', 'task')
        msg = (
            f'`{name}` declares a task for `@graph` bodies and never runs standalone; '
            + 'launch it with `run` or `run_get_node`, or place the call in a graph.'
        )
        raise GraphError(msg)

    @property
    def process_class(self) -> type[TaskProcess]:
        """Return the task process class behind the decorated function."""
        # `_build_task` always decorates with `TaskProcess` as the base class.
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
        """Rebuild the task from a checkpoint; the persistence layer calls this, not users."""
        return self._function.recreate_from(*args, **kwargs)


class CalcJobTaskHandle:
    """A `CalcJob` subclass carrying its graph declaration, launched with per-placement metadata."""

    is_process_function: t.ClassVar[bool] = False

    def __init__(
        self,
        process_class: type[CalcJob],
        *,
        inputs: PortDeclaration | None = None,
        outputs: PortDeclaration | None = None,
    ) -> None:
        self._process_class: type[CalcJob] = process_class
        self._task_spec: TaskIR = TaskIR.from_process(
            process_class,
            declared_inputs=_declared_shape(inputs),
            declared_outputs=_declared_shape(outputs, leaves=True),
        )
        self._task_spec.check_ports()
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

    def __init__(
        self,
        process_class: type[WorkChain],
        *,
        inputs: PortDeclaration | None = None,
        outputs: PortDeclaration | None = None,
    ) -> None:
        self._process_class: type[WorkChain] = process_class
        self._task_spec: TaskIR = TaskIR.from_process(
            process_class,
            declared_inputs=_declared_shape(inputs),
            declared_outputs=_declared_shape(outputs, leaves=True),
        )
        self._task_spec.check_ports()
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


def _needs_metadata(task: t.Any) -> t.TypeGuard[ProcessTask]:
    """Return whether a placement dispatches a `CalcJob` directly."""
    from aiida.engine.processes.graphs.ir import ProcessTask

    if not isinstance(task, ProcessTask):
        return False
    return issubclass(task.spec.process_class, CalcJob)


def _merge_task_metadata(
    task: ProcessTask, provided: Mapping[str, t.Any], inputs: dict[str, t.Any]
) -> dict[str, t.Any]:
    """Merge the stashed per-placement `CalcJob` metadata, failing loudly when absent."""
    placement = task.name
    try:
        metadata = provided[placement]
    except KeyError:
        msg = (
            f'task `{placement}` is a `CalcJob` and needs launch metadata; '
            f"pass it keyed by placement name, e.g. `task_metadata={{'{placement}': {{...}}}}`."
        )
        raise GraphValidationError(msg) from None
    if not isinstance(metadata, Mapping):
        msg = f'task `{placement}` metadata must be a mapping of metadata inputs, not `{type(metadata)}`.'
        raise GraphValidationError(msg)
    # The stash wins: graph-wired inputs never carry `metadata` (it is excluded from the
    # graph contract and popped at launch).
    return {**inputs, 'metadata': dict(metadata)}


def _check_task_contract(
    function: type[CalcJob] | type[WorkChain] | Callable[..., t.Any],
    *,
    declares_ports: bool,
) -> None:
    """Reject task declarations the graph runtime cannot represent.

    Process classes check their ports when their task declaration is built.
    """
    if is_process_function(function):
        msg = 'tasks take plain functions, not decorated process functions; pass the undecorated function instead.'
        raise GraphTypeCheckError(msg)
    if inspect.isclass(function) and issubclass(function, (CalcJob, WorkChain)):
        try:
            validate_link_label(function.__name__)
        except ValueError as exception:
            msg = (
                f'declaration name `{function.__name__}` is invalid as a link label ({exception}); '
                + 'use alphanumerics and underscores without leading or trailing underscores instead'
            )
            raise GraphTypeCheckError(msg) from exception
        return
    if declares_ports:
        msg = 'task functions declare their ports through annotations; `inputs` and `outputs` apply to process classes.'
        raise GraphTypeCheckError(msg)
    if inspect.isclass(function):
        msg = 'tasks accept functions, a `CalcJob` subclass, or a `WorkChain` subclass; not other process classes.'
        raise GraphTypeCheckError(msg)
    signature = inspect.signature(function)
    if 'after' in signature.parameters:
        msg = '`after` is reserved for source graph ordering dependencies.'
        raise GraphTypeCheckError(msg)
    hints = t.get_type_hints(function, include_extras=True)
    annotation = hints.get('return', inspect.Signature.empty)
    if _is_structured(annotation):
        msg = 'task output namespaces are not supported; declare leaf outputs instead.'
        raise GraphTypeCheckError(msg)
    if annotation is inspect.Signature.empty:
        msg = (
            'tasks require a return annotation to wire their outputs; '
            'annotate the function or wrap third-party functions in an annotated one.'
        )
        raise GraphTypeCheckError(msg)


def _build_task(
    function: type[CalcJob] | type[WorkChain] | Callable[P, R],
    *,
    inputs: PortDeclaration | None = None,
    outputs: PortDeclaration | None = None,
) -> CalcJobTaskHandle | WorkChainTaskHandle | FunctionTaskHandle[P, R]:
    """Construct a task handle with static leaf outputs and fixed graph inputs."""
    _check_task_contract(function, declares_ports=bool(inputs or outputs))
    if inspect.isclass(function) and issubclass(function, CalcJob):
        return CalcJobTaskHandle(function, inputs=inputs, outputs=outputs)
    if inspect.isclass(function) and issubclass(function, WorkChain):
        return WorkChainTaskHandle(function, inputs=inputs, outputs=outputs)
    assert not inspect.isclass(function)
    decorated = process_function(node_class=CalcFunctionNode, base_class=TaskProcess)(function)
    typevar_inputs, typevar_output = _typevar_positions(function)
    handle = FunctionTaskHandle(decorated, typevar_inputs=typevar_inputs, typevar_output=typevar_output)
    spec = handle.process_class.spec()
    _reject_dynamic_inputs(spec.inputs)
    if any(isinstance(port, PortNamespace) for port in spec.outputs.values()):
        msg = 'tasks require static leaf outputs; declare leaf outputs instead.'
        raise GraphTypeCheckError(msg)
    return handle
