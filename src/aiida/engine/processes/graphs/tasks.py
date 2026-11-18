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
from dataclasses import dataclass
from types import UnionType

from typing_extensions import is_typeddict

from aiida.common.exceptions import GraphError, GraphTypeCheckError, GraphValidationError
from aiida.common.lang import override
from aiida.common.links import validate_link_label
from aiida.common.loaders import get_object_loader
from aiida.engine.processes.calcjobs import CalcJob
from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum
from aiida.engine.processes.functions import FunctionProcessBase, P, ProcessFunctionType, process_function
from aiida.engine.processes.generic.ports import UNSPECIFIED, Port
from aiida.engine.processes.graphs.ir import TaskIR, TypevarPositions
from aiida.engine.processes.graphs.results import Err, Ok, Result, _error_contract, _error_types, _result_contract
from aiida.engine.processes.graphs.shapes import (
    LeafShape,
    NamespaceShape,
    _expanded_annotation,
    _forward_marker,
    _is_type_var,
)
from aiida.engine.processes.port_model import (
    _as_port_model,
    _field_from_annotation,
    _is_structured,
    _namespace_value,
    _without_marks,
)
from aiida.engine.processes.ports import PortNamespace, _infer_node_types, _owned_container_type, _runtime_value
from aiida.engine.processes.process import Process
from aiida.engine.processes.process_spec import GraphProcessSpec, ProcessSpec
from aiida.engine.processes.workchains.workchain import WorkChain
from aiida.engine.utils import is_process_function
from aiida.orm import CalcFunctionNode, CalcJobNode, Data, DataList, EnumData, WorkChainNode, to_aiida_type
from aiida.orm.nodes.data.datanode import DataNode

__all__ = (
    'CalcJobTaskHandle',
    'FunctionTaskHandle',
    'PlacementHandle',
    'PortDeclaration',
    'TaskProcess',
    'WorkChainTaskHandle',
)


R = t.TypeVar('R')
_V = t.TypeVar('_V')
_E = t.TypeVar('_E')


def _validate_alias_name(name: object) -> str:
    """Return an explicit placement name, checked against the call link-label contract."""
    if not isinstance(name, str):
        msg = f'placement alias must be a quoted name, not `{name!r}`; pass one literal string instead.'
        raise GraphTypeCheckError(msg)
    try:
        validate_link_label(name)
    except ValueError as exception:
        msg = (
            f'placement alias `{name}` is invalid as a link label ({exception}); '
            + 'use alphanumerics and underscores without leading or trailing underscores instead'
        )
        raise GraphTypeCheckError(msg) from exception
    return name


@dataclass(frozen=True, slots=True)
class PlacementHandle(t.Generic[P, R]):
    """A declaration paired with an explicit, immutable graph placement name."""

    target: Callable[P, R]
    placement_name: str

    def __post_init__(self) -> None:
        _validate_alias_name(self.placement_name)

    @t.overload
    def __call__(
        self: PlacementHandle[P, Result[_V, _E]], *args: P.args, **kwargs: P.kwargs
    ) -> tuple[_V, _E | None]: ...

    @t.overload
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

    @t.overload
    def __call__(self: PlacementHandle[P, R], *args: t.Any, after: t.Any = ..., **kwargs: t.Any) -> R: ...

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        """Delegate direct calls without changing the declaration's execution contract."""
        return self.target(*args, **kwargs)


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


PortDeclaration: t.TypeAlias = Mapping[str, 'type[DataNode] | tuple[type[DataNode], ...] | PortDeclaration']
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
        types = tuple(kind for kind in given if inspect.isclass(kind) and issubclass(kind, DataNode))
        if not types or len(types) != len(given):
            msg = f'declared port `{location}` takes `DataNode` subclasses, not `{value!r}`.'
            raise GraphTypeCheckError(msg)
        fields.append((name, LeafShape(types=types)))
    return NamespaceShape(fields=tuple(fields))


def _declare_output_ports(return_annotation: t.Any, spec: ProcessSpec) -> None:
    """Declare static output ports from the return annotation.

    A scalar annotation declares one ``result`` port; a total ``TypedDict`` declares one
    port per key. Task registration rejects missing declarations and dynamic namespaces.

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
            spec.output(key, valid_type=_infer_node_types(hint) or (DataNode,))
        return
    if t.get_origin(return_annotation) is tuple or return_annotation is tuple:
        msg = 'name multiple task outputs with a TypedDict instead of a tuple.'
        raise GraphTypeCheckError(msg)
    if _is_structured(return_annotation):
        spec.outputs_from(return_annotation)
        return
    spec.output(
        Process.SINGLE_OUTPUT_LINKNAME,
        valid_type=_infer_node_types(return_annotation) or (DataNode,),
    )


class TaskProcess(FunctionProcessBase):
    """Task process with plain Python inputs and static outputs."""

    _allow_persistence = True
    """Task children checkpoint on daemon workers; the generated class travels as bytes."""

    _spec_class: type[GraphProcessSpec] = GraphProcessSpec
    # Set at declaration: a total `TypedDict` or a `PortModel` return declares one port per field.
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
        return_annotation = annotations.get('return')
        annotation, codes = _result_contract(return_annotation)
        for label, code in codes.items():
            if label in spec.exit_codes or any(existing.status == code.status for existing in spec.exit_codes.values()):
                msg = f'task exit code `{label}` ({code.status}) conflicts with an engine exit code.'
                raise GraphTypeCheckError(msg)
            assert code.message is not None
            spec.exit_code(code.status, label, code.message, invalidates_cache=code.invalidates_cache)
        if t.get_origin(return_annotation) is Result:
            success = _as_port_model(annotation)
            if _is_structured(success):
                spec.outputs_from(t.cast(type, success), prefix='value.')
                spec.outputs['value'].required = False
            else:
                spec.output('value', valid_type=_infer_node_types(annotation) or (Data,), required=False)
            spec.output('error', valid_type=EnumData, required=False)
            spec.outputs.dynamic = False
            cls._named_outputs = False
            return
        _declare_output_ports(return_annotation, spec)
        spec.outputs.dynamic = False
        cls._named_outputs = is_typeddict(return_annotation) or _is_structured(return_annotation)

    @override
    def _function_arguments(self) -> tuple[list[t.Any], dict[str, t.Any]]:
        args, kwargs = super()._function_arguments()
        bound = inspect.signature(self._func).bind(*args, **kwargs)
        hints = t.get_type_hints(self._func, include_extras=True)
        for name, value in bound.arguments.items():
            kind = _owned_container_type(hints.get(name))
            if kind is not None and isinstance(value, kind):
                bound.arguments[name] = list(value) if kind is DataList else dict(value.items())
        return list(bound.args), bound.kwargs

    @override
    def _prepare_result(self, result: t.Any) -> t.Any:
        annotation = t.get_type_hints(self._func, include_extras=True).get('return')
        _, codes = _result_contract(annotation)
        if t.get_origin(annotation) is not Result:
            if isinstance(result, Result):
                msg = 'task exit codes must be declared in a Result return annotation.'
                raise GraphValidationError(msg)
            return super()._prepare_result(result)
        if isinstance(result, Ok):
            return self._prepare_ok(result, annotation)
        if isinstance(result, Err):
            return self._prepare_error(result, annotation, codes)
        msg = 'a task annotated with Result must return `Ok` outputs or `Err` error.'
        raise GraphValidationError(msg)

    def _prepare_ok(self, result: Ok[t.Any, t.Any], annotation: t.Any) -> ExitCode:
        """Store successful outputs and exit cleanly."""
        if isinstance(result.value, (ExitCode, Result)):
            msg = 'Ok must contain task outputs, not an exit code or another Result.'
            raise GraphValidationError(msg)
        success = t.get_args(annotation)[0]
        if result.value is None and success is not type(None) and type(None) not in t.get_args(success):
            msg = 'the successful Result type does not allow None.'
            raise GraphValidationError(msg)
        if result.value is None:
            # No value arm is stored; dependents read the absent arm as `None`.
            return ExitCode()
        if _is_structured(_as_port_model(success)):
            self._store_value(self.spec().outputs['value'], result.value, 'value')
            return ExitCode()
        self._store_leaf(self.spec().outputs['value'], result.value, 'value')
        return ExitCode()

    def _store_value(self, port: Port | PortNamespace, value: t.Any, path: str) -> None:
        """Store one success arm under its dotted path, expanding namespaces."""
        value = _namespace_value(value)
        if isinstance(port, PortNamespace):
            self._store_namespace(port, value, path)
        else:
            self._store_leaf(port, value, path)

    def _store_namespace(self, port: PortNamespace, value: t.Any, path: str) -> None:
        """Store the declared fields of one namespace arm, rejecting undeclared and missing fields."""
        if value is None:
            if port.required:
                msg = f'task value `{path}` is required but missing.'
                raise GraphValidationError(msg)
            return
        if not isinstance(value, Mapping):
            msg = f'task value `{path}` must match its declared output namespace.'
            raise GraphValidationError(msg)
        extra = [name for name in value if name not in port]
        if extra:
            msg = f'task value `{path}` returned undeclared outputs {extra}; return only declared outputs.'
            raise GraphValidationError(msg)
        for name, child in port.items():
            if name in value:
                self._store_value(child, value[name], f'{path}.{name}')
            elif child.required:
                msg = f'task value is missing required output `{path}.{name}`.'
                raise GraphValidationError(msg)

    def _store_leaf(self, port: Port, value: t.Any, path: str) -> None:
        """Store one leaf arm; `None` stores nothing, so only an optional port admitting it accepts it."""
        if value is not None:
            stored = _runtime_value(port.valid_type, value)
            self.out(path, stored if isinstance(stored, DataNode) else to_aiida_type(stored))
            return
        if port.required:
            msg = (
                f'task value `{path}` is a required output and cannot be None; '
                'return a value or make the field optional with a default.'
            )
            raise GraphValidationError(msg)
        kinds = port.valid_type
        if type(None) not in ((kinds,) if isinstance(kinds, type) else kinds or ()):
            msg = f'task value `{path}` does not allow None.'
            raise GraphValidationError(msg)

    def _store_named(self, outputs: PortNamespace, value: Mapping[str, t.Any]) -> None:
        """Store a mapping return by output name, rejecting undeclared and missing required outputs."""
        missing = [name for name, port in outputs.items() if port.required and name not in value]
        if missing:
            msg = f'task omitted required outputs {missing}; return every required output.'
            raise GraphValidationError(msg)
        extra = [name for name in value if name not in outputs]
        if extra:
            msg = f'task returned undeclared outputs {extra}; return only declared outputs.'
            raise GraphValidationError(msg)
        for name, port in outputs.items():
            if name in value:
                self._store_value(port, value[name], name)

    def _prepare_error(self, result: Err[t.Any, t.Any], annotation: t.Any, codes: Mapping[str, ExitCode]) -> ExitCode:
        """Store the declared error member and exit with its code."""
        error = result.error
        kinds = _error_types(t.get_args(annotation)[1])
        if isinstance(error, ExitCodeEnum):
            if not isinstance(error, kinds):
                msg = f'task returned an error from an undeclared enum: {error!r}.'
                raise GraphValidationError(msg)
            error = error.value
        if isinstance(error, ExitCode) and any(
            error.status == code.status and error.invalidates_cache == code.invalidates_cache for code in codes.values()
        ):
            member = next(member for kind in kinds for member in kind if member.value.status == error.status)
            stored = to_aiida_type(member)
            stored.label = f'{type(member).__name__}.{member.name}'
            self.out('error', stored)
            return error
        msg = f'task returned an undeclared exit code: {error!r}.'
        raise GraphValidationError(msg)

    @override
    def _out_result(self, result: t.Any) -> None:
        outputs = self.spec().outputs
        names = list(outputs)
        value = _namespace_value(result)
        if isinstance(value, Mapping) and self._named_outputs:
            # Named outputs fill by key; a model instance converts to its mapping first,
            # and a structured input returned unchanged already is one.
            self._store_named(outputs, value)
            return
        if self._named_outputs and not isinstance(value, Mapping):
            msg = f'task declares named outputs {names} but returned a single value; return a mapping instead.'
            raise GraphValidationError(msg)
        values = result if isinstance(result, tuple) else (result,)
        if not names and result is None:
            return
        if len(values) != len(names):
            msg = f'task declares {len(names)} outputs {names} but returned {len(values)} values.'
            raise GraphValidationError(msg)
        stored: dict[str, DataNode] = {}
        for name, value in zip(names, values, strict=True):
            converted = _runtime_value(outputs[name].valid_type, value)
            stored[name] = converted if isinstance(converted, DataNode) else to_aiida_type(converted)
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
        exit_codes: Mapping[str, ExitCode] | None = None,
    ) -> None:
        self._function: ProcessFunctionType[P, R, CalcFunctionNode] = function
        self._task_spec: TaskIR = TaskIR.from_process(
            function, typevar_inputs=typevar_inputs, typevar_output=typevar_output, exit_codes=exit_codes
        )
        # Copy name and docstring, not the function state: the handle owns its task spec.
        functools.update_wrapper(self, function, updated=())

    @t.overload
    def __call__(
        self: FunctionTaskHandle[P, Result[_V, _E]], *args: P.args, **kwargs: P.kwargs
    ) -> tuple[_V, _E | None]: ...

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

    def alias(self, name: str) -> PlacementHandle[P, R]:
        """Return an immutable handle placing this task under an explicit placement name."""
        return PlacementHandle(self, name)


class CalcJobTaskHandle:
    """A `CalcJob` subclass carrying its graph declaration and execution input contract."""

    is_process_function: t.ClassVar[bool] = False

    def __init__(
        self,
        process_class: type[CalcJob],
        *,
        inputs: PortDeclaration | None = None,
        outputs: PortDeclaration | None = None,
        exit_codes: Mapping[str, ExitCode] | None = None,
        error_enums: tuple[str, ...] | None = None,
    ) -> None:
        self._process_class: type[CalcJob] = process_class
        self._task_spec: TaskIR = TaskIR.from_process(
            process_class,
            declared_inputs=_declared_shape(inputs),
            declared_outputs=_declared_shape(outputs, leaves=True),
            exit_codes=exit_codes,
            error_enums=error_enums,
        )
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

    def alias(self, name: str) -> PlacementHandle[t.Any, t.Any]:
        """Return an immutable handle placing this task under an explicit placement name."""
        return PlacementHandle(self, name)


class WorkChainTaskHandle:
    """A `WorkChain` subclass carrying its graph declaration and execution input contract."""

    is_process_function: t.ClassVar[bool] = False

    def __init__(
        self,
        process_class: type[WorkChain],
        *,
        inputs: PortDeclaration | None = None,
        outputs: PortDeclaration | None = None,
        exit_codes: Mapping[str, ExitCode] | None = None,
        error_enums: tuple[str, ...] | None = None,
    ) -> None:
        self._process_class: type[WorkChain] = process_class
        self._task_spec: TaskIR = TaskIR.from_process(
            process_class,
            declared_inputs=_declared_shape(inputs),
            declared_outputs=_declared_shape(outputs, leaves=True),
            exit_codes=exit_codes,
            error_enums=error_enums,
        )
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

    def alias(self, name: str) -> PlacementHandle[t.Any, t.Any]:
        """Return an immutable handle placing this task under an explicit placement name."""
        return PlacementHandle(self, name)


def _error_codes(errors: type[ExitCodeEnum] | UnionType) -> tuple[dict[str, ExitCode], tuple[str, ...]]:
    """Validate a task-level error declaration and return its codes and enum identifiers.

    The declaration mirrors the error half of a `Result` annotation, so unions
    qualify their labels and duplicate statuses fail here, not at runtime.
    """
    kinds = _error_types(errors)
    return _error_contract(kinds), tuple(get_object_loader().identify_object(kind) for kind in kinds)


def _check_task_contract(
    function: type[CalcJob] | type[WorkChain] | Callable[..., t.Any],
    *,
    declares_ports: bool,
    outputs: PortDeclaration | None = None,
    errors: type[ExitCodeEnum] | UnionType | None = None,
) -> None:
    """Reject task declarations the graph runtime cannot represent.

    Ports are checked when the task declaration is built, in `TaskIR.from_process`.
    """
    if is_process_function(function):
        msg = 'tasks take plain functions, not decorated process functions; pass the undecorated function instead.'
        raise GraphTypeCheckError(msg)
    if errors is not None and not (inspect.isclass(function) and issubclass(function, (CalcJob, WorkChain))):
        msg = 'task errors belong in the `Result` return annotation; `errors` applies to process classes.'
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
        if errors is not None and ('error' in function.spec().outputs or 'error' in (outputs or {})):
            msg = (
                f'`{function.__name__}` already declares an `error` output, which the declared failure arm needs; '
                + 'map its failures with a wrapping work chain, or drop `errors`'
            )
            raise GraphTypeCheckError(msg)
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
    returned = hints.get('return', inspect.Signature.empty)
    annotation, _ = _result_contract(returned)
    if t.get_origin(returned) is Result and (t.get_origin(annotation) is tuple or annotation is tuple):
        msg = 'name multiple task outputs with a TypedDict instead of a tuple.'
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
    errors: type[ExitCodeEnum] | UnionType | None = None,
) -> CalcJobTaskHandle | WorkChainTaskHandle | FunctionTaskHandle[P, R]:
    """Construct a task handle with static outputs and fixed graph inputs."""
    _check_task_contract(function, declares_ports=bool(inputs or outputs), outputs=outputs, errors=errors)
    if inspect.isclass(function) and issubclass(function, CalcJob):
        exit_codes, error_enums = _error_codes(errors) if errors is not None else ({}, ())
        return CalcJobTaskHandle(
            function, inputs=inputs, outputs=outputs, exit_codes=exit_codes, error_enums=error_enums
        )
    if inspect.isclass(function) and issubclass(function, WorkChain):
        exit_codes, error_enums = _error_codes(errors) if errors is not None else ({}, ())
        return WorkChainTaskHandle(
            function, inputs=inputs, outputs=outputs, exit_codes=exit_codes, error_enums=error_enums
        )
    assert not inspect.isclass(function)
    decorated = process_function(node_class=CalcFunctionNode, base_class=TaskProcess)(function)
    typevar_inputs, typevar_output = _typevar_positions(function)
    _, exit_codes = _result_contract(t.get_type_hints(function, include_extras=True).get('return'))
    return FunctionTaskHandle(
        decorated, typevar_inputs=typevar_inputs, typevar_output=typevar_output, exit_codes=exit_codes
    )
