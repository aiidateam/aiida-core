###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Static graph declarations, independent of scheduling and source authoring."""

from __future__ import annotations

import abc
import base64
import contextlib
import sys
import typing as t
from collections.abc import Mapping
from copy import copy, deepcopy
from dataclasses import dataclass, field, replace
from functools import cached_property

from typing_extensions import is_typeddict

from aiida.common import _callables as callables
from aiida.common.exceptions import GraphTypeCheckError
from aiida.common.lang import override
from aiida.common.loaders import get_object_loader
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.graphs.expressions import infer_expression_shape
from aiida.engine.processes.graphs.inputs import _port_for_shape, _shape_from_port
from aiida.engine.processes.graphs.operations import (
    BINARY_OPERATIONS,
    CONSTANT_PORT,
    LEFT_PORT,
    OPERAND_PORT,
    OPERATIONS,
    RESULT_PORT,
    RIGHT_PORT,
    OperationKind,
    const_result_shape,
)
from aiida.engine.processes.graphs.results import Result, _result_contract
from aiida.engine.processes.graphs.shapes import (
    LeafShape,
    NamespaceShape,
    Shape,
    dump_shape,
    load_shape,
    shape_for_annotation,
)
from aiida.engine.processes.ports import InputPort, OutputPort, PortNamespace, _infer_node_types, _node_type
from aiida.engine.processes.process import Process
from aiida.orm import Code, DataDict, DataList
from aiida.orm.nodes.data.datanode import DataNode

__all__ = (
    'BodyTask',
    'BranchControl',
    'Dependency',
    'Endpoint',
    'GraphIR',
    'GraphTask',
    'InlineOperation',
    'LoopControl',
    'MapControl',
    'OptionalOutputNamespace',
    'OutputTree',
    'ProcessTask',
    'Route',
    'SubgraphTask',
    'TaskIR',
)

_GRAPH_IR_EXPRESSION_VERSION: t.Final = '0.3'
_GRAPH_IR_OUTPUT_TREE_VERSION: t.Final = '0.5'
_GRAPH_IR_RESULT_VERSION: t.Final = '0.4'
_GRAPH_IR_VERSION: t.Final = '0.2'
_GRAPH_IR_LEGACY_VERSION: t.Final = '0.1'
_TASK_IR_VERSION: t.Final = '0.1'
_CONDITION_PORT: t.Final = 'condition'
_TaskKind: t.TypeAlias = t.Literal['process', 'graph', 'branch', 'loop', 'map', 'operation']


def _require_version(version: object, supported: str, what: str) -> str:
    """Reject declarations whose format this implementation cannot read."""
    if version != supported:
        msg = f'cannot read a {what} declaration of version `{version}`; supported version is `{supported}`.'
        raise GraphTypeCheckError(msg)
    return supported


def _port_at(ports: PortNamespace, path: str) -> InputPort | OutputPort | PortNamespace | None:
    """Find a declared path, without treating dynamic ports as known names."""
    port: t.Any = ports
    for segment in path.split('.') if path else ():
        if not isinstance(port, PortNamespace) or segment not in port:
            return None
        port = port[segment]
    return port


def _ancestry_required(ports: PortNamespace, path: str) -> bool:
    """Return whether every namespace enclosing a declared path is required."""
    port: t.Any = ports
    for segment in path.split('.')[:-1]:
        port = port[segment]
        if not port.required:
            return False
    return True


def _reject_dynamic_inputs(ports: PortNamespace, process_class: type[Process], path: tuple[str, ...] = ()) -> None:
    """Require fixed scientific namespaces, not externally configurable execution namespaces."""
    from aiida.engine.processes.calcjobs import CalcJob
    from aiida.engine.processes.workchains.workchain import WorkChain

    if issubclass(process_class, (CalcJob, WorkChain)) and _is_runtime_config_path(
        process_class, process_class.spec().inputs, path
    ):
        return
    if ports.dynamic and ports.required:
        msg = f'graph tasks require fixed inputs; namespace `{ports.name}` is dynamic.'
        raise GraphTypeCheckError(msg)
    for name, child in ports.items():
        if isinstance(child, PortNamespace) and not child.is_metadata and (child.required or not child.dynamic):
            _reject_dynamic_inputs(child, process_class, (*path, name))


def _reject_dynamic_outputs(ports: PortNamespace) -> None:
    """Reject dynamic output namespaces at any depth; graph outputs stay fixed."""
    if ports.dynamic:
        msg = (
            'graph tasks require static outputs, not dynamic outputs; '
            'declare the outputs of a dynamic namespace with `task(..., outputs={...})`.'
        )
        raise GraphTypeCheckError(msg)
    for child in ports.values():
        if isinstance(child, PortNamespace):
            _reject_dynamic_outputs(child)


def _narrowed_port(port: InputPort | OutputPort | PortNamespace, shape: Shape) -> InputPort | OutputPort | None:
    """Return a copy of a static leaf narrowed to the solved types, or `None` when incompatible."""
    if isinstance(port, PortNamespace) or not isinstance(shape, LeafShape) or shape.types is None:
        return None
    existing = port.valid_type
    existing = (existing,) if isinstance(existing, type) else tuple(existing or ())
    if existing and not all(any(issubclass(kind, expected) for expected in existing) for kind in shape.types):
        return None
    narrowed = copy(port)
    narrowed.valid_type = shape.types
    return narrowed


def _close_dynamic(
    ports: PortNamespace,
    declared: NamespaceShape,
    port_class: type[InputPort] | type[OutputPort],
    path: str = '',
    *,
    narrow: bool = False,
) -> PortNamespace:
    """Return a copy of ``ports`` whose dynamic namespaces hold exactly the declared fields.

    The class spec is shared by every placement, so declared ports go into a copy: a namespace
    receiving new names becomes static, and every other port is kept as is. Solved generic
    outputs narrow matching static leaves instead, when ``narrow`` holds.
    """
    closed = PortNamespace(ports.name, help=ports.help, required=ports.required)
    for name, child in ports.items():
        closed[name] = child
    added = False
    for name, shape in declared.fields:
        location = f'{path}.{name}' if path else name
        existing = ports.get(name)
        if isinstance(existing, PortNamespace) and isinstance(shape, NamespaceShape):
            nested = _close_dynamic(existing, shape, port_class, location)
            closed[name] = nested
            if not nested.dynamic:
                added = True
            continue
        if existing is not None:
            narrowed = _narrowed_port(existing, shape) if narrow else None
            if narrowed is not None:
                closed[name] = narrowed
                added = True
                continue
            msg = f'`{location}` is already a declared port; declare only names inside dynamic namespaces.'
            raise GraphTypeCheckError(msg)
        if not ports.dynamic:
            msg = f'`{location}` lies in a static namespace; declare only names inside dynamic namespaces.'
            raise GraphTypeCheckError(msg)
        added = True
        if isinstance(shape, NamespaceShape):
            nested = PortNamespace(name, dynamic=True, valid_type=ports.valid_type)
            closed[name] = _close_dynamic(nested, shape, port_class, location)
            continue
        allowed = ports.valid_type
        if allowed is not None and not all(issubclass(kind, allowed) for kind in shape.types or ()):
            msg = f'`{location}` declares types outside those its dynamic namespace accepts: {allowed}.'
            raise GraphTypeCheckError(msg)
        closed[name] = port_class(name, valid_type=shape.types, required=True)
    if ports.dynamic and not added:
        closed.dynamic = True
        closed.valid_type = ports.valid_type
    return closed


def _static_inputs(process_class: type[Process], declared: NamespaceShape) -> PortNamespace:
    """Return the fixed input ports of a task process, rejecting dynamic namespaces."""
    ports = process_class.spec().inputs
    if declared.fields:
        ports = _close_dynamic(ports, declared, InputPort)
    _reject_dynamic_inputs(ports, process_class)
    return ports


def _static_outputs(process_class: type[Process], declared: NamespaceShape) -> PortNamespace:
    """Return the static output ports of a task process, rejecting dynamic namespaces."""
    ports = process_class.spec().outputs
    if declared.fields:
        ports = _close_dynamic(ports, declared, OutputPort, narrow=True)
    _reject_dynamic_outputs(ports)
    return ports


def _code_only_types(valid_type: t.Any) -> bool:
    """Return whether every accepted non-`None` type is an `orm.Code` subclass.

    At least one non-`None` type is required, so unconstrained ports, empty
    declarations, and mixed scientific unions never classify from the type alone.
    """
    kinds = valid_type if isinstance(valid_type, (tuple, list)) else (valid_type,)
    kept = tuple(kind for kind in kinds if kind is not None and kind is not type(None))
    return bool(kept) and all(isinstance(kind, type) and issubclass(kind, Code) for kind in kept)


def _is_runtime_config_path(
    process_class: type[Process],
    ports: PortNamespace,
    segments: tuple[str, ...],
    seen: frozenset[type[Process]] | None = None,
) -> bool:
    """Return whether one concrete input path may be supplied by runtime configuration.

    Classification reads the declared process specification, not values or name
    heuristics: base-process roots, `Code`-typed leaves at any depth, and
    exposure chains preserving both. A removed port never
    classifies; an exposed `CalcJob` namespace alone does not make its
    scientific siblings configuration-capable.
    """
    from aiida.engine.processes.calcjobs import CalcJob
    from aiida.engine.processes.workchains.workchain import WorkChain

    if not segments or _port_at(ports, '.'.join(segments)) is None:
        return False
    base = CalcJob if issubclass(process_class, CalcJob) else WorkChain
    if segments[0] in base.spec().inputs:
        return True
    port = _port_at(ports, '.'.join(segments))
    if _code_only_types(getattr(port, 'valid_type', None)):
        return True
    return _is_exposed_runtime_path(process_class, segments, seen or frozenset())


def _is_exposed_runtime_path(
    process_class: type[Process], segments: tuple[str, ...], seen: frozenset[type[Process]]
) -> bool:
    """Return whether an input path classifies through an `expose_inputs` chain."""
    if process_class in seen:
        return False
    seen = seen | {process_class}
    for namespace, source_class, absorbed in process_class.spec().input_exposures():
        if not issubclass(source_class, Process):
            continue
        prefix = tuple(namespace.split('.')) if namespace else ()
        if len(segments) <= len(prefix) or tuple(segments[: len(prefix)]) != prefix:
            continue
        rest = segments[len(prefix) :]
        if rest[0] not in absorbed:
            continue
        if _is_runtime_config_path(source_class, source_class.spec().inputs, rest, seen):
            return True
    return False


def _input_ports_at(task: GraphTask, path: str) -> list[t.Any]:
    """Return the declared ports one placement path resolves to.

    A branch condition is a synthetic port wired outside either side's declared inputs, so it
    resolves to nothing here. A loop condition instead names loop state declared by the body
    namespace, and resolves through it like any other input.
    """
    if isinstance(task, BranchControl) and path == task.condition_port:
        return []
    try:
        namespaces = task.input_ports()
    except GraphTypeCheckError as exception:
        msg = f'task `{task.name}` declares ports the spec cannot represent.'
        raise GraphTypeCheckError(msg) from exception
    return [port for namespace in namespaces if (port := _port_at(namespace, path)) is not None]


@dataclass(frozen=True)
class ExecutorReference:
    """The importable name of a decorated task function, with an optional pickled executor."""

    module: str
    name: str
    payload: str | None = None

    def load(self) -> type[Process]:
        """Return the task process class, preferring a pickled executor over re-import."""
        if self.payload is not None:
            try:
                loaded = callables.loads(base64.b64decode(self.payload))
            except Exception as exception:
                msg = (
                    f'executor payload for `{self.module}:{self.name}` could not be deserialized '
                    f'({exception}); keep task declarations importable on the daemon.'
                )
                raise ImportError(msg) from exception
            if isinstance(loaded, type) and issubclass(loaded, Process):
                return loaded
            msg = f'executor payload for `{self.module}:{self.name}` did not resolve to a task process.'
            raise ImportError(msg)
        loaded = get_object_loader().load_object(f'{self.module}:{self.name}')
        if getattr(loaded, 'is_process_function', False):
            return loaded.process_class
        if isinstance(loaded, type) and issubclass(loaded, Process):
            return loaded
        msg = f'`{self.module}:{self.name}` does not resolve to a task process; keep task declarations importable.'
        raise ImportError(msg)

    def to_dict(self) -> dict[str, str]:
        """Return the executor reference without the live process class."""
        if self.payload is None:
            return {'module': self.module, 'name': self.name}
        return {'module': self.module, 'name': self.name, 'payload': self.payload}

    @classmethod
    def from_dict(cls, data: Mapping[str, str]) -> ExecutorReference:
        """Rebuild an executor reference from its serialized form."""
        return cls(module=data['module'], name=data['name'], payload=data.get('payload'))


TypevarPositions: t.TypeAlias = dict[t.Any, list[str]]
"""Bare type variables mapped to the input ports declaring them."""


def _overlay_element(base: Shape, annotated: Shape | None) -> Shape:
    """Overlay collection members from ``annotated`` onto ``base``, keeping base types."""
    if annotated is None:
        return base
    if isinstance(base, LeafShape) and isinstance(annotated, LeafShape):
        if annotated.element is None:
            return base
        return replace(base, element=annotated.element)
    if isinstance(base, NamespaceShape) and isinstance(annotated, NamespaceShape):
        by_name = dict(annotated.fields)
        return replace(
            base,
            fields=tuple((name, _overlay_element(child, by_name.get(name))) for name, child in base.fields),
        )
    return base


def _task_func_annotations(process_class: type[Process]) -> dict[str, t.Any] | None:
    """Return the task function hints, or `None` when unavailable or unresolvable."""
    func = getattr(process_class, '_func', None)
    if func is None or not callable(func):
        return None
    try:
        return t.get_type_hints(func, include_extras=True)
    except (NameError, TypeError, SyntaxError):
        # String annotations name objects outside the task module; only ports describe the contract then.
        return None


def _shape_for_success(annotation: t.Any) -> Shape | None:
    """Expand a success annotation, naming `TypedDict` outputs per key."""
    if not is_typeddict(annotation):
        return shape_for_annotation(annotation)
    try:
        hints = t.get_type_hints(annotation, include_extras=True)
    except (NameError, TypeError, SyntaxError):
        return None
    return NamespaceShape(fields=tuple((key, shape_for_annotation(hints.get(key))) for key in hints))


def _with_input_elements(process_class: type[Process], shape: NamespaceShape) -> NamespaceShape:
    """Overlay hint members onto input ``shape``; ports keep types and requiredness."""
    hints = _task_func_annotations(process_class)
    if not hints:
        return shape
    annotated = {name: shape_for_annotation(hint) for name, hint in hints.items() if name != 'return'}
    if not annotated:
        return shape
    return replace(
        shape, fields=tuple((name, _overlay_element(child, annotated.get(name))) for name, child in shape.fields)
    )


def _with_result_elements(process_class: type[Process], shape: Shape) -> Shape:
    """Overlay return-annotation members onto result ``shape``; the `Result` error arm is untouched."""
    hints = _task_func_annotations(process_class)
    if not hints or 'return' not in hints:
        return shape
    success, _ = _result_contract(hints['return'])
    annotated = _shape_for_success(success)
    if annotated is None:
        return shape
    if t.get_origin(hints['return']) is Result and isinstance(shape, NamespaceShape):
        return replace(
            shape,
            fields=tuple(
                (name, _overlay_element(child, annotated) if name == 'value' else child) for name, child in shape.fields
            ),
        )
    return _overlay_element(shape, annotated)


@dataclass(frozen=True)
class TaskIR:
    """A task's executor and its static input/output contracts.

    ``declared_inputs`` and ``declared_outputs`` fix the names and types inside dynamic
    namespaces of the process spec, so the task contract stays static.
    ``typevar_inputs`` and ``typevar_output`` serve lowering only: solved types land in
    ``declared_outputs``, so neither is serialized nor compared.
    """

    identifier: str
    executor: ExecutorReference
    declared_inputs: NamespaceShape = field(default_factory=NamespaceShape)
    declared_outputs: NamespaceShape = field(default_factory=NamespaceShape)
    typevar_inputs: TypevarPositions = field(default_factory=dict, compare=False)
    typevar_output: t.Any = field(default=None, compare=False)
    exit_codes: dict[str, ExitCode] = field(default_factory=dict)
    error_enums: tuple[str, ...] = field(default_factory=tuple)
    result_errors: tuple[str, ...] = ()
    result_nullable: bool = False
    version: str = _TASK_IR_VERSION

    def __post_init__(self) -> None:
        """Normalize containers so copies compare equal on this frozen dataclass."""
        object.__setattr__(self, 'exit_codes', dict(self.exit_codes))
        object.__setattr__(self, 'error_enums', tuple(self.error_enums))

    @classmethod
    def from_process(
        cls,
        process: t.Callable[..., t.Any],
        *,
        declared_inputs: NamespaceShape | None = None,
        declared_outputs: NamespaceShape | None = None,
        typevar_inputs: TypevarPositions | None = None,
        typevar_output: t.Any | None = None,
        exit_codes: Mapping[str, ExitCode] | None = None,
        error_enums: tuple[str, ...] | None = None,
        result_errors: tuple[str, ...] = (),
        result_nullable: bool = False,
    ) -> TaskIR:
        """Reference a decorated task function, a `CalcJob` subclass, or a `WorkChain` subclass.

        Every task handle builds its declaration here, so the static port contract is checked once.
        The check reads the live class: loading the payload while the task module imports would
        overwrite the module's classes with their pickled state.

        :raises GraphTypeCheckError: if the inputs or outputs include a dynamic namespace.
        """
        module, name = process.__module__, process.__name__
        # Payloads travel with the template, so executors from notebooks, sibling modules, or any
        # uninstalled location resolve without re-import; import-by-reference stays the fallback.
        process_class = getattr(process, 'process_class', None)
        if not (isinstance(process_class, type) and issubclass(process_class, Process)):
            process_class = process if (isinstance(process, type) and issubclass(process, Process)) else None
        inputs: NamespaceShape = declared_inputs or NamespaceShape()
        outputs: NamespaceShape = declared_outputs or NamespaceShape()
        payload: str | None = None
        if process_class is not None:
            _static_inputs(process_class, inputs)
            _static_outputs(process_class, outputs)
            import cloudpickle

            module_object = sys.modules.get(module)
            ours = module_object is not None and module not in cloudpickle.list_registry_pickle_by_value()
            if ours:
                cloudpickle.register_pickle_by_value(module_object)
            try:
                with contextlib.suppress(TypeError):
                    payload = base64.b64encode(callables.dumps(process_class)).decode('ascii')
            finally:
                if ours:
                    cloudpickle.unregister_pickle_by_value(module_object)
        return cls(
            identifier=name,
            executor=ExecutorReference(module, name, payload),
            declared_inputs=inputs,
            declared_outputs=outputs,
            typevar_inputs=typevar_inputs or {},
            typevar_output=typevar_output,
            exit_codes=dict(exit_codes or {}),
            error_enums=tuple(error_enums or ()),
            result_errors=result_errors,
            result_nullable=result_nullable,
        )

    @cached_property
    def process_class(self) -> type[Process]:
        """Return the task process class loaded from its executor reference."""
        return self.executor.load()

    @property
    def inputs(self) -> PortNamespace:
        """Return the fixed input ports of the task process."""
        return _static_inputs(self.process_class, self.declared_inputs)

    @property
    def outputs(self) -> PortNamespace:
        """Return the static output ports of the task process.

        Process classes declaring error enums expose a synthetic `error` arm,
        so failed children branch the same way `Result` tasks do. The arm
        carries no process port; it only names the declared failure.
        """
        ports = _static_outputs(self.process_class, self.declared_outputs)
        if self.exit_codes and 'error' not in ports:
            ports = _with_error_arm(ports)
        if self.error_enums:
            ports = _optional_success_arms(ports)
        return ports

    @property
    def result_port(self) -> str:
        """Return the single leaf output port, or `''` when the result is the whole outputs namespace."""
        outputs: PortNamespace = self.outputs
        if len(outputs) != 1:
            return ''
        name, port = next(iter(outputs.items()))
        # A namespace result binds whole, so dotted reads select from the task outputs.
        return '' if isinstance(port, PortNamespace) else name

    @property
    def input_shape(self) -> NamespaceShape:
        """Return the fixed input contracts as nested shapes, with annotation elements."""
        shape = _shape_from_port(self.inputs)
        assert isinstance(shape, NamespaceShape)
        return _with_input_elements(self.process_class, shape)

    @property
    def result_shape(self) -> Shape:
        """Return the result port contracts, with annotation elements, or the whole outputs namespace."""
        selected = self.outputs[self.result_port] if self.result_port else self.outputs
        assert isinstance(selected, (InputPort, OutputPort, PortNamespace))
        return _with_result_elements(self.process_class, _shape_from_port(selected))

    def runtime_input_paths(self) -> frozenset[str]:
        """Return the minimal input path prefixes runtime configuration may supply.

        An unwired input at or beneath each prefix may be bound externally through
        `runtime_config` instead of graph wiring. Base-process roots, `Code`-typed
        leaves at any depth, and `expose_inputs` chains preserving both are
        covered; scientific siblings of an exposed namespace are not. Plain
        function tasks classify nothing, so the set is empty for them.

        :return: the topmost configuration-capable dotted input paths.
        """
        from aiida.engine.processes.calcjobs import CalcJob
        from aiida.engine.processes.workchains.workchain import WorkChain

        process_class = self.process_class
        if not (issubclass(process_class, CalcJob) or issubclass(process_class, WorkChain)):
            return frozenset()
        ports = self.inputs
        found: set[str] = set()

        def visit(namespace: PortNamespace, prefix: str) -> None:
            """Collect the topmost configuration-capable paths without descending beneath them."""
            for name, child in namespace.items():
                path = f'{prefix}.{name}' if prefix else name
                if _is_runtime_config_path(process_class, ports, tuple(path.split('.'))):
                    found.add(path)
                elif isinstance(child, PortNamespace):
                    visit(child, path)

        visit(ports, '')
        return frozenset(found)

    def to_dict(self) -> dict[str, t.Any]:
        """Return the task declaration without the live process class."""
        data: dict[str, t.Any] = {'identifier': self.identifier, 'executor': self.executor.to_dict()}
        if self.declared_inputs.fields:
            data['declared_inputs'] = dump_shape(self.declared_inputs)
        if self.declared_outputs.fields:
            data['declared_outputs'] = dump_shape(self.declared_outputs)
        if self.exit_codes:
            data['exit_codes'] = {label: code._asdict() for label, code in self.exit_codes.items()}
        if self.error_enums:
            data['error_enums'] = list(self.error_enums)
        if self.result_errors:
            data['result_errors'] = list(self.result_errors)
            data['result_nullable'] = self.result_nullable
        return {**data, 'version': self.version}

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> TaskIR:
        """Rebuild a task declaration from its serialized form."""
        return cls(
            identifier=data['identifier'],
            executor=ExecutorReference.from_dict(data['executor']),
            declared_inputs=_load_declared(data.get('declared_inputs')),
            declared_outputs=_load_declared(data.get('declared_outputs')),
            exit_codes={label: ExitCode(**code) for label, code in data.get('exit_codes', {}).items()},
            error_enums=tuple(data.get('error_enums', ())),
            result_errors=tuple(data.get('result_errors', ())),
            result_nullable=data.get('result_nullable', False),
            version=_require_version(data.get('version'), _TASK_IR_VERSION, 'task'),
        )


def _dump_output_tree(source: OutputTree) -> dict[str, t.Any]:
    """Serialize one output leaf or nested mapping, preserving the endpoint shape."""
    if isinstance(source, dict):
        return {'nested': {name: _dump_output_tree(child) for name, child in source.items()}}
    if isinstance(source, OptionalOutputNamespace):
        return {'presence': source.presence.to_dict(), **_dump_output_tree(source.fields)}
    return source.to_dict()


def _load_output_tree(data: Mapping[str, t.Any]) -> OutputTree:
    """Rebuild one output leaf or nested mapping from its serialized form."""
    if 'nested' in data:
        nested = data['nested']
        if not isinstance(nested, Mapping):
            msg = 'malformed graph declaration; nested outputs must form a mapping.'
            raise GraphTypeCheckError(msg)
        children: Mapping[str, t.Any] = nested
        fields = {name: _load_output_tree(child) for name, child in children.items()}
        if 'presence' in data:
            return OptionalOutputNamespace(Endpoint.from_dict(data['presence']), fields)
        return fields
    return Endpoint.from_dict(data)


def _output_required(origin: InputPort | OutputPort) -> bool:
    """Return whether a regrouped output leaf always holds a stored node.

    Outputs regroup existing nodes instead of creating data. A leaf stays
    required only when its source must hold a node: a required contract whose
    types exclude `None`. Anything else may resolve to no node and stays out
    of the required contract, so the emission simply omits it.
    """
    if not origin.required:
        return False
    types = origin.valid_type
    if types is None:
        # An unrestricted input accepts `None`; a required process output always holds a node.
        return isinstance(origin, OutputPort)
    if isinstance(types, type):
        return types is not type(None)
    return type(None) not in types


def _output_namespace_from_origin(name: str, origin: PortNamespace, *, required: bool) -> PortNamespace:
    """Copy a task namespace's output contract without flattening away its optionality."""
    result = PortNamespace(name, required=required)
    for key, child in origin.items():
        if isinstance(child, PortNamespace):
            result[key] = _output_namespace_from_origin(key, child, required=child.required)
        else:
            result[key] = OutputPort(key, valid_type=child.valid_type, required=_output_required(child))
    return result


def _with_error_arm(ports: PortNamespace) -> PortNamespace:
    """Return a copy of ``ports`` with a synthetic `error` arm for declared failures."""
    from aiida.orm import EnumData

    fresh = PortNamespace(ports.name, help=ports.help, required=ports.required)
    for name, child in ports.items():
        fresh[name] = child
    fresh['error'] = OutputPort('error', valid_type=EnumData, required=False)
    return fresh


def _optional_success_arms(ports: PortNamespace) -> PortNamespace:
    """Return a copy of ``ports`` with every success arm optional for mapped failures.

    A mapped failure leaves its success arms absent; like `Result` arms they travel
    as `None`. Presence on the success path stays enforced by the runtime
    missing-output check for declared outputs, not by the port contract.
    """
    optional = PortNamespace(ports.name, help=ports.help, required=ports.required)
    for name, child in ports.items():
        if name == 'error' or not child.required:
            optional[name] = child
            continue
        relaxed = copy(child)
        relaxed.required = False
        optional[name] = relaxed
    return optional


def _branch_condition(
    data: Mapping[str, t.Any],
) -> tuple[t.Literal['truthy', 'is_none', 'is_not_none', 'is_member', 'is_not_member'], tuple[str, str] | None]:
    """Return the stored branch condition, defaulting to the pre-test truthiness check."""
    stored_member = data.get('condition_member')
    member = tuple(stored_member) if stored_member is not None else None
    if member is not None and len(member) != 2:
        msg = 'a branch `condition_member` names an enum identifier and member name pair.'
        raise GraphTypeCheckError(msg)
    return data.get('condition_test', 'truthy'), t.cast('tuple[str, str] | None', member)


def _load_declared(data: Mapping[str, t.Any] | None) -> NamespaceShape:
    """Restore a dynamic-namespace declaration, empty when none was stored."""
    if data is None:
        return NamespaceShape()
    shape = load_shape(data)
    if not isinstance(shape, NamespaceShape):
        msg = 'malformed task declaration; declared ports must form a namespace.'
        raise GraphTypeCheckError(msg)
    return shape


class Route(t.NamedTuple):
    """A graph input routed to one task input port."""

    task: str
    port: str


@dataclass(frozen=True)
class Endpoint:
    """A task output, or a graph input passed through unchanged."""

    port: str
    task: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Return the endpoint as a task name and port pair."""
        return {'task': self.task, 'port': self.port}

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> Endpoint:
        """Rebuild an endpoint from its serialized form."""
        try:
            return cls(task=data['task'], port=data['port'])
        except KeyError as exception:
            msg = f'malformed endpoint declaration; missing key {exception}.'
            raise GraphTypeCheckError(msg) from exception


@dataclass(frozen=True)
class Dependency:
    """A value dependency, or an ordering dependency with neither port named."""

    source: str
    target: str
    source_port: str | None = None
    target_port: str | None = None

    def __post_init__(self) -> None:
        if (self.source_port is None) != (self.target_port is None):
            msg = 'a dependency must name both ports, or neither port for explicit ordering.'
            raise GraphTypeCheckError(msg)

    @property
    def carried_between(self) -> tuple[str, str] | None:
        """Return the valued ports, or `None` for an ordering dependency."""
        if self.source_port is None or self.target_port is None:
            return None
        return self.source_port, self.target_port

    def to_dict(self) -> dict[str, str | None]:
        """Return the dependency as task names with optional ports."""
        return {
            'source': self.source,
            'target': self.target,
            'source_port': self.source_port,
            'target_port': self.target_port,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> Dependency:
        """Rebuild a dependency from its serialized form."""
        try:
            return cls(
                source=data['source'],
                target=data['target'],
                source_port=data.get('source_port'),
                target_port=data.get('target_port'),
            )
        except KeyError as exception:
            msg = f'malformed dependency declaration; missing key {exception}.'
            raise GraphTypeCheckError(msg) from exception


@dataclass(frozen=True, kw_only=True)
class GraphTask(abc.ABC):
    """A named process or control-flow task with directly supplied inputs.

    `Task` nodes execute something (a process or a nested template run once);
    `Control` nodes dispatch bodies without executing anything themselves.
    """

    KIND: t.ClassVar[_TaskKind]
    name: str
    inputs: dict[str, t.Any] = field(default_factory=dict)

    @property
    def kind(self) -> _TaskKind:
        """Return the placement kind."""
        return self.KIND

    @abc.abstractmethod
    def input_ports(self) -> tuple[PortNamespace, ...]:
        """Return the contracts accepted by this placement."""

    @abc.abstractmethod
    def output_ports(self) -> PortNamespace:
        """Return the static outputs produced by this placement."""

    def to_dict(self) -> dict[str, t.Any]:
        """Return the placement without its kind-specific declaration."""
        return {'name': self.name, 'kind': self.kind, 'inputs': deepcopy(self.inputs)}

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> GraphTask:
        """Rebuild the placement matching the stored kind."""
        try:
            common = {'name': data['name'], 'inputs': data.get('inputs', {})}
            kind = data.get('kind')
            if kind == 'process':
                return ProcessTask(
                    spec=TaskIR.from_dict(data['spec']), capture_error=data.get('capture_error', False), **common
                )
            body = GraphIR.from_dict(data['body']) if kind in ('graph', 'branch', 'loop') else None
            if kind == 'graph':
                if body is None:
                    msg = 'malformed graph task declaration; missing body.'
                    raise GraphTypeCheckError(msg)
                return SubgraphTask(body=body, capture_error=data.get('capture_error', False), **common)
            if kind == 'branch':
                if body is None:
                    msg = 'malformed graph task declaration; missing body.'
                    raise GraphTypeCheckError(msg)
                condition_test, condition_member = _branch_condition(data)
                return BranchControl(
                    body=body,
                    otherwise=GraphIR.from_dict(data['otherwise']),
                    condition_port=data.get('condition_port', _CONDITION_PORT),
                    condition_test=condition_test,
                    condition_member=condition_member,
                    **common,
                )
            if kind == 'loop':
                if body is None:
                    msg = 'malformed graph task declaration; missing body.'
                    raise GraphTypeCheckError(msg)
                return LoopControl(
                    body=body,
                    condition_port=data.get('condition_port', _CONDITION_PORT),
                    max_iterations=data['max_iterations'],
                    **common,
                )
            if kind == 'operation':
                return InlineOperation.from_dict(data)
            if kind == 'map':
                nested = GraphIR.from_dict(data['body']) if data.get('body') is not None else None
                mapped = TaskIR.from_dict(data['spec']) if data.get('spec') is not None else None
                return MapControl(
                    spec=mapped,
                    body=nested,
                    container=data['container'],
                    element=data.get('element'),
                    **common,
                )
        except KeyError as exception:
            msg = f'malformed graph task declaration; missing key {exception}.'
            raise GraphTypeCheckError(msg) from exception
        msg = f'unsupported graph task kind `{kind}`.'
        raise GraphTypeCheckError(msg)


@dataclass(frozen=True, kw_only=True)
class BodyTask(GraphTask):
    """A placement whose executor is a nested graph template.

    Closed dispatch in `GraphTask.from_dict` only rebuilds the known kinds;
    subclassing alone does not register a new one. Never instantiated directly.
    """

    body: GraphIR

    def __post_init__(self) -> None:
        """Reject direct instantiation with a loud ``TypeError``."""
        if type(self) is BodyTask:
            msg = 'BodyTask is abstract; subclass it and set KIND.'
            raise TypeError(msg)

    @override
    def input_ports(self) -> tuple[PortNamespace, ...]:
        """Return the input contracts of the nested template."""
        return (self.body.build_input_namespace(),)

    @override
    def output_ports(self) -> PortNamespace:
        """Return the output contracts of the nested template."""
        return self.body.build_output_namespace()

    @override
    def to_dict(self) -> dict[str, t.Any]:
        """Return the placement with its nested template."""
        return {**super().to_dict(), 'body': self.body.to_dict()}


@dataclass(frozen=True, kw_only=True)
class SubgraphTask(BodyTask):
    """An inlined graph with its own invocation boundary."""

    KIND: t.ClassVar[_TaskKind] = 'graph'
    capture_error: bool = False

    @override
    def output_ports(self) -> PortNamespace:
        ports = super().output_ports()
        if not self.capture_error:
            return ports
        success = copy(ports[self.body.result_port] if self.body.result_port else ports)
        success.required = False
        arms = PortNamespace('outputs')
        arms['value'] = success
        return _with_error_arm(arms)

    @override
    def to_dict(self) -> dict[str, t.Any]:
        data = super().to_dict()
        if self.capture_error:
            data['capture_error'] = True
        return data


@dataclass(frozen=True, kw_only=True)
class BranchControl(BodyTask):
    """A condition dispatching exactly one of two nested templates.

    ``condition_port`` is a synthetic port wired outside either side's declared inputs, so it
    never appears in their declared inputs. ``condition_test`` records how the condition
    selects a side: truthiness, a presence test against `None`, or an identity
    test against one declared error member, named by ``condition_member`` as an
    enum identifier and member name pair.
    """

    KIND: t.ClassVar[_TaskKind] = 'branch'
    condition_port: str = _CONDITION_PORT
    otherwise: GraphIR
    condition_test: t.Literal['truthy', 'is_none', 'is_not_none', 'is_member', 'is_not_member'] = 'truthy'
    condition_member: tuple[str, str] | None = None

    def __post_init__(self) -> None:
        """Reject unknown condition tests and member tests without exactly one error member."""
        if self.condition_test not in ('truthy', 'is_none', 'is_not_none', 'is_member', 'is_not_member'):
            msg = f'unsupported branch condition test `{self.condition_test}`.'
            raise GraphTypeCheckError(msg)
        if (self.condition_test in ('is_member', 'is_not_member')) != (self.condition_member is not None):
            msg = 'member tests need exactly one declared error member.'
            raise GraphTypeCheckError(msg)

    @property
    def branches(self) -> tuple[GraphIR, ...]:
        """Return the branch bodies, taken side first."""
        return self.body, self.otherwise

    @override
    def input_ports(self) -> tuple[PortNamespace, ...]:
        """Return the input contracts of each side template."""
        return tuple(branch.build_input_namespace() for branch in self.branches)

    @override
    def output_ports(self) -> PortNamespace:
        """Return the output contracts of a continuing arm, if there is one."""
        arm = next((branch for branch in self.branches if not branch.always_returns), self.body)
        return arm.build_output_namespace()

    @override
    def to_dict(self) -> dict[str, t.Any]:
        """Return the placement with both side templates and the condition port."""
        return {
            **super().to_dict(),
            'condition_port': self.condition_port,
            'condition_test': self.condition_test,
            'condition_member': list(self.condition_member) if self.condition_member is not None else None,
            'otherwise': self.otherwise.to_dict(),
        }


@dataclass(frozen=True, kw_only=True)
class LoopControl(BodyTask):
    """A condition iterating one nested template with numbered child runs.

    ``condition_port`` names loop state, not a synthetic port: it must be declared in the body
    inputs (the routed initial state) and returned in the body outputs (the updated check).
    It shares the serialized ``condition_port`` key with branches; renaming it would break
    the stored declaration schema.
    """

    KIND: t.ClassVar[_TaskKind] = 'loop'
    condition_port: str = _CONDITION_PORT
    max_iterations: int = 1000

    @override
    def to_dict(self) -> dict[str, t.Any]:
        return {**super().to_dict(), 'condition_port': self.condition_port, 'max_iterations': self.max_iterations}


@dataclass(frozen=True, kw_only=True)
class MapControl(GraphTask):
    """A fan-out applying one task or graph to every element of an owned container.

    ``collection`` is the input port receiving the ``DataList``/``DataDict`` wire; exactly one
    of ``spec`` (a task) or ``body`` (a nested graph) carries the mapped callable.
    ``container`` records the lowered collection kind, so the single ``result`` output keeps it.
    The scheduler dispatches one child per element plus a collector calculation that creates
    the result container; the graph itself only returns that existing container.

    A plain ``par_map(task, values)`` maps a unary callable and leaves ``element`` unset.
    A ``partial`` map binds every input but one, naming the remaining input in ``element``:
    each element wires into ``element`` while the bound inputs travel with every item through
    the normal ``inputs`` and dependency wires. ``element`` is ``None`` for legacy unary maps.
    """

    KIND: t.ClassVar[_TaskKind] = 'map'
    spec: TaskIR | None = None
    body: GraphIR | None = None
    container: t.Literal['list', 'dict'] = 'list'
    element: str | None = None

    def __post_init__(self) -> None:
        """Reject maps that do not carry exactly one mapped callable of a known container kind."""
        if (self.spec is None) == (self.body is None):
            msg = 'maps carry exactly one mapped callable: a task `spec` or a nested graph `body`.'
            raise GraphTypeCheckError(msg)
        if self.container not in ('list', 'dict'):
            msg = f'maps collect `list` or `dict` containers, not `{self.container}`.'
            raise GraphTypeCheckError(msg)

    @property
    def fixed_names(self) -> tuple[str, ...]:
        """Return the bound input names travelling with every item, or `()` for unary maps."""
        if self.element is None:
            return ()
        return tuple(name for name, _ in self.mapped_inputs.fields if name != self.element)

    @property
    def mapped_inputs(self) -> NamespaceShape:
        """Return the input contract the mapped callable applies to each element."""
        if self.spec is not None:
            return self.spec.input_shape
        if self.body is not None:
            return self.body.input_shape
        msg = f'map `{self.name}` carries exactly one mapped callable: a task `spec` or a nested graph `body`.'
        raise GraphTypeCheckError(msg)

    @property
    def mapped_result_port(self) -> str:
        """Return the single output port the mapped callable produces per element."""
        if self.spec is not None:
            return self.spec.result_port
        if self.body is not None:
            return self.body.result_port
        msg = f'map `{self.name}` carries exactly one mapped callable: a task `spec` or a nested graph `body`.'
        raise GraphTypeCheckError(msg)

    @override
    def input_ports(self) -> tuple[PortNamespace, ...]:
        """Return the collection input plus every `partial`-bound fixed input.

        The mapped element itself is never wired: it arrives from the collection, so only
        ``collection`` and the bound inputs resolve here. A bound input named ``collection``
        would collide with the collection wire and is rejected when the map is lowered.
        """
        namespace = PortNamespace('inputs')
        namespace['collection'] = InputPort('collection', valid_type=(DataList, DataDict))
        if self.element is not None:
            source = self.spec.inputs if self.spec is not None else self._body_inputs()
            for name in self.fixed_names:
                port = source.get(name)
                if port is None:
                    msg = (
                        f'map `{self.name}` wires `{name}`, '
                        'which is not an input of the mapped callable; check the spelling instead.'
                    )
                    raise GraphTypeCheckError(msg)
                namespace[name] = port
        return (namespace,)

    def _body_inputs(self) -> PortNamespace:
        """Return the input contracts of the mapped nested graph."""
        if self.body is None:
            msg = f'map `{self.name}` carries exactly one mapped callable: a task `spec` or a nested graph `body`.'
            raise GraphTypeCheckError(msg)
        return self.body.build_input_namespace()

    @override
    def output_ports(self) -> PortNamespace:
        """Return the single result container of the lowered collection kind."""
        collected = (DataList,) if self.container == 'list' else (DataDict,)
        namespace = PortNamespace('outputs')
        namespace['result'] = OutputPort('result', valid_type=collected)
        return namespace

    @override
    def to_dict(self) -> dict[str, t.Any]:
        """Return the placement with its mapped callable, container kind, and bound element."""
        data: dict[str, t.Any] = {
            **super().to_dict(),
            'spec': self.spec.to_dict() if self.spec is not None else None,
            'body': self.body.to_dict() if self.body is not None else None,
            'container': self.container,
        }
        if self.element is not None:
            data['element'] = self.element
        return data


@dataclass(frozen=True, kw_only=True)
class ProcessTask(GraphTask):
    """A decorated task function dispatched as one child process."""

    KIND: t.ClassVar[_TaskKind] = 'process'
    spec: TaskIR
    capture_error: bool = False

    @override
    def input_ports(self) -> tuple[PortNamespace, ...]:
        """Return the fixed input contracts of the task process."""
        return (self.spec.inputs,)

    @override
    def output_ports(self) -> PortNamespace:
        """Return the static outputs of the task process."""
        ports = self.spec.outputs
        if self.spec.result_errors and not self.capture_error:
            success = copy(ports['value'])
            success.required = not self.spec.result_nullable
            ports = PortNamespace('outputs')
            ports['value'] = success
        return ports

    @override
    def to_dict(self) -> dict[str, t.Any]:
        """Return the placement with its task declaration."""
        data = {**super().to_dict(), 'spec': self.spec.to_dict()}
        if self.capture_error:
            data['capture_error'] = True
        return data


@dataclass(frozen=True)
class OptionalOutputNamespace:
    """A group of output endpoints emitted only if its source namespace is present."""

    presence: Endpoint
    fields: dict[str, OutputTree]


OutputTree: t.TypeAlias = 'Endpoint | OptionalOutputNamespace | dict[str, OutputTree]'


def _has_optional_output_namespace(tree: OutputTree) -> bool:
    """Check whether the output needs a namespace presence guard."""
    return isinstance(tree, OptionalOutputNamespace) or (
        isinstance(tree, dict) and any(_has_optional_output_namespace(child) for child in tree.values())
    )


"""A leaf endpoint or a nested mapping of those regrouping existing nodes."""


@dataclass(frozen=True, kw_only=True)
class InlineOperation(GraphTask):
    """A scalar operator evaluated inline by the engine, without a child process.

    The operand contracts live in ``input_shape`` (``left`` and ``right`` for binary
    operators, ``operand`` for unary ones); ``result_shape`` types the single ``result``
    output. Both shapes serialize with the shared shape helpers, like every other task.
    """

    KIND: t.ClassVar[_TaskKind] = 'operation'
    operation: OperationKind
    input_shape: NamespaceShape
    result_shape: LeafShape
    expression: dict[str, t.Any] | None = None

    def __post_init__(self) -> None:
        """Reject unknown operators and operand contracts the operator cannot read."""
        if self.operation != 'expression' and self.operation not in OPERATIONS:
            msg = f'unknown operation `{self.operation}`; expected one of {sorted(OPERATIONS)} or expression.'
            raise GraphTypeCheckError(msg)
        if self.operation == 'expression':
            if self.expression is None:
                msg = 'an inline collection expression requires an expression tree.'
                raise GraphTypeCheckError(msg)
            inferred = infer_expression_shape(self.expression, dict(self.input_shape.fields))
            if inferred != self.result_shape:
                msg = 'inline expression result does not match its inferred contract.'
                raise GraphTypeCheckError(msg)
            return
        if self.expression is not None:
            msg = 'only expression placements carry an expression tree.'
            raise GraphTypeCheckError(msg)
        if self.operation == 'const':
            self._check_const()
            return
        expected = (LEFT_PORT, RIGHT_PORT) if self.operation in BINARY_OPERATIONS else (OPERAND_PORT,)
        names = tuple(name for name, _ in self.input_shape.fields)
        if sorted(names) != sorted(expected):
            msg = f'operation `{self.operation}` reads operand(s) {list(expected)}, not {list(names)}.'
            raise GraphTypeCheckError(msg)
        for name, shape in self.input_shape.fields:
            if not isinstance(shape, LeafShape):
                msg = f'operation `{self.operation}` reads scalar leaves; `{name}` is a namespace.'
                raise GraphTypeCheckError(msg)

    def _check_const(self) -> None:
        """Reject bound values that are no finite scalar, and results outside their contract."""
        names = tuple(name for name, _ in self.input_shape.fields)
        if sorted(names) != [CONSTANT_PORT]:
            msg = f'operation `const` binds one value under `{CONSTANT_PORT}`, not {list(names)}.'
            raise GraphTypeCheckError(msg)
        if set(self.inputs) != {CONSTANT_PORT}:
            msg = f'operation `const` carries its bound value under `{CONSTANT_PORT}`.'
            raise GraphTypeCheckError(msg)
        bound = const_result_shape(self.inputs[CONSTANT_PORT])
        bound_types = bound.types or ()
        if tuple(self.result_shape.types or ()) != tuple(bound_types):
            declared = ', '.join(f'`{kind.__name__}`' for kind in self.result_shape.types or ()) or 'untyped'
            bound_name = bound_types[0].__name__ if bound_types else 'untyped'
            msg = f'operation `const` declares result {declared} but binds `{bound_name}`.'
            raise GraphTypeCheckError(msg)

    @property
    def result_port(self) -> str:
        """Return the single output port."""
        return RESULT_PORT

    @override
    def input_ports(self) -> tuple[PortNamespace, ...]:
        """Return the fixed operand contracts of the operator."""
        namespace = _port_for_shape('inputs', self.input_shape)
        assert isinstance(namespace, PortNamespace)
        return (namespace,)

    @override
    def output_ports(self) -> PortNamespace:
        """Return the single result output of the operator."""
        namespace = PortNamespace('outputs')
        namespace[RESULT_PORT] = OutputPort(RESULT_PORT, valid_type=self.result_shape.types)
        return namespace

    @override
    def to_dict(self) -> dict[str, t.Any]:
        """Return the placement with its operator and operand contracts."""
        return {
            **super().to_dict(),
            'operation': self.operation,
            'input_shape': dump_shape(self.input_shape),
            'result_shape': dump_shape(self.result_shape),
            **({'expression': self.expression} if self.expression is not None else {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> InlineOperation:
        """Rebuild an operation placement from its serialized form."""
        try:
            input_shape = load_shape(data['input_shape'])
            result_shape = load_shape(data['result_shape'])
            if not isinstance(input_shape, NamespaceShape):
                msg = 'malformed operation task declaration; operands form a namespace of scalar leaves.'
                raise GraphTypeCheckError(msg)
            if not isinstance(result_shape, LeafShape):
                msg = 'malformed operation task declaration; the result is one scalar leaf.'
                raise GraphTypeCheckError(msg)
            return cls(
                name=data['name'],
                inputs=data.get('inputs', {}),
                operation=data['operation'],
                input_shape=input_shape,
                result_shape=result_shape,
                expression=data.get('expression'),
            )
        except KeyError as exception:
            msg = f'malformed operation task declaration; missing key {exception}.'
            raise GraphTypeCheckError(msg) from exception


def _task_contains_operation(task: GraphTask, *, expression_only: bool = False) -> bool:
    """Return whether a placement evaluates an inline operation, at any nesting depth."""
    if isinstance(task, InlineOperation):
        return not expression_only or task.operation == 'expression'
    if isinstance(task, MapControl):
        return task.body is not None and _graph_contains_operation(task.body, expression_only=expression_only)
    if isinstance(task, BranchControl):
        return _graph_contains_operation(task.body, expression_only=expression_only) or _graph_contains_operation(
            task.otherwise, expression_only=expression_only
        )
    if isinstance(task, BodyTask):
        return _graph_contains_operation(task.body, expression_only=expression_only)
    return False


def _graph_contains_operation(graph: GraphIR, *, expression_only: bool = False) -> bool:
    """Return whether any placement of a template evaluates an inline operation."""
    return any(_task_contains_operation(task, expression_only=expression_only) for task in graph.tasks)


def _select_shape(shape: Shape, path: str) -> Shape | None:
    """Return the nested contracts at a dotted path, or `None` when absent."""
    current = shape
    for segment in path.split('.') if path else ():
        if not isinstance(current, NamespaceShape):
            return None
        try:
            current = current.select(segment)
        except KeyError:
            return None
    return current


def _relative_shape(shape: Shape, prefix: str, port: str) -> Shape | None:
    """Return source contracts for an endpoint port relative to a task or body result."""
    if prefix:
        if port == prefix:
            return shape
        if port.startswith(f'{prefix}.') and isinstance(shape, LeafShape) and isinstance(shape.element, NamespaceShape):
            return _select_shape(shape.element, port[len(prefix) + 1 :])
        return None
    return _select_shape(shape, port) if isinstance(shape, NamespaceShape) else None


def _normalized_value_types(types: tuple[type, ...]) -> tuple[t.Any, ...]:
    """Return element types with ORM/Python spellings unified (`int` reads as `Int`)."""
    return tuple(_node_type(kind) if _node_type(kind) is not None else kind for kind in types)


def _leaf_types_agree(first: tuple[type, ...] | None, second: tuple[type, ...] | None) -> bool:
    """Return whether two known value contracts accept each other, ignoring unknown sides."""
    if first is None or second is None:
        return True
    try:
        expected, received = _normalized_value_types(first), _normalized_value_types(second)
        return all(any(issubclass(kind, other) for other in received) for kind in expected) and all(
            any(issubclass(kind, other) for other in expected) for kind in received
        )
    except TypeError:
        return tuple(first) == tuple(second)


def branch_shapes_agree(first: Shape, second: Shape) -> bool:
    """Return whether two branch outputs agree on value types, recursing into members.

    Requiredness, defaults, and documentation are intentionally ignored: only the value
    contracts matter. An unknown side (`None` types or a missing member) agrees with
    anything, so callers must not claim the known side from such agreement.
    """
    if isinstance(first, NamespaceShape) and isinstance(second, NamespaceShape):
        if {name for name, _ in first.fields} != {name for name, _ in second.fields}:
            return False
        other = dict(second.fields)
        return all(branch_shapes_agree(child, other[name]) for name, child in first.fields)
    if isinstance(first, LeafShape) and isinstance(second, LeafShape):
        if not _leaf_types_agree(first.types, second.types):
            return False
        if first.element is None or second.element is None:
            return True
        return branch_shapes_agree(first.element, second.element)
    return False


def collection_members_agree(first: Shape, second: Shape) -> bool:
    """Compare collection members without rechecking scalar port compatibility."""
    if isinstance(first, NamespaceShape) and isinstance(second, NamespaceShape):
        other = dict(second.fields)
        return all(name in other and collection_members_agree(child, other[name]) for name, child in first.fields)
    if isinstance(first, LeafShape) and isinstance(second, LeafShape):
        if first.element is None or second.element is None:
            return True
        return branch_shapes_agree(first.element, second.element)
    return False


def merge_branch_shape(first: Shape | None, second: Shape | None) -> Shape | None:
    """Return the branch output contract without fabricating a known member from one arm."""
    if first is None or second is None or not branch_shapes_agree(first, second):
        return None
    if isinstance(first, NamespaceShape) and isinstance(second, NamespaceShape):
        other = dict(second.fields)
        merged = tuple((name, merge_branch_shape(child, other[name])) for name, child in first.fields)
        if any(shape is None for _, shape in merged):
            return None
        return replace(first, fields=tuple((name, t.cast('Shape', shape)) for name, shape in merged))
    if isinstance(first, LeafShape) and isinstance(second, LeafShape):
        if first.types is None or second.types is None:
            return replace(first, types=None, element=None)
        if first.element is None:
            return first
        if second.element is None:
            return replace(first, element=None)
        merged_element = merge_branch_shape(first.element, second.element)
        if merged_element is None:
            return None
        return replace(first, element=merged_element)
    return None


@dataclass(frozen=True)
class GraphIR:
    """A static graph template, with fixed inputs and nested outputs regrouping nodes."""

    tasks: tuple[GraphTask, ...]
    input_shape: NamespaceShape
    dependencies: tuple[Dependency, ...] = ()
    inputs: dict[str, tuple[Route, ...]] = field(default_factory=dict)
    outputs: dict[str, OutputTree] = field(default_factory=dict)
    identifier: str | None = None
    version: str = _GRAPH_IR_VERSION
    output_typehints: dict[str, tuple[type, ...]] = field(default_factory=dict)
    return_outputs: dict[str, OutputTree] | None = None
    return_typehints: dict[str, tuple[type, ...]] = field(default_factory=dict)
    return_error: tuple[str, str] | None = None

    def __post_init__(self) -> None:
        # Imported here: validation reads this module's port helpers at runtime.
        from aiida.engine.processes.graphs.validate import validate_graph

        validate_graph(self)
        if (
            self.has_return
            or any(_has_optional_output_namespace(tree) for tree in self.outputs.values())
            or any(body.version == _GRAPH_IR_OUTPUT_TREE_VERSION for body in self._child_templates())
        ):
            version = _GRAPH_IR_OUTPUT_TREE_VERSION
        elif self._uses_result_policy:
            version = _GRAPH_IR_RESULT_VERSION
        elif _graph_contains_operation(self, expression_only=True):
            version = _GRAPH_IR_EXPRESSION_VERSION
        else:
            version = _GRAPH_IR_VERSION if _graph_contains_operation(self) else _GRAPH_IR_LEGACY_VERSION
        if self.version != version:
            object.__setattr__(self, 'version', version)

    @property
    def has_return(self) -> bool:
        """Whether this region ends with an explicit invocation return."""
        return self.return_outputs is not None or self.return_error is not None

    @cached_property
    def always_returns(self) -> bool:
        """Whether a successfully executed region can never reach its join."""
        return self.has_return or any(
            isinstance(task, BranchControl) and all(arm.always_returns for arm in task.branches) for task in self.tasks
        )

    def _child_templates(self, *, regions_only: bool = False) -> t.Iterator[GraphIR]:
        """Yield immediate child templates, optionally staying within the invocation."""
        for task in self.tasks:
            if isinstance(task, BranchControl):
                yield from task.branches
            elif isinstance(task, LoopControl) or (not regions_only and isinstance(task, SubgraphTask)):
                yield task.body
            elif not regions_only and isinstance(task, MapControl) and task.body is not None:
                yield task.body

    def success_returns(self) -> t.Iterator[GraphIR]:
        """Yield the explicit success-return sites of this invocation."""
        if self.return_outputs is not None:
            yield self
        for region in self._child_templates(regions_only=True):
            yield from region.success_returns()

    @cached_property
    def _uses_result_policy(self) -> bool:
        """Version this template if it requires the new invocation semantics."""
        for task in self.tasks:
            if isinstance(task, ProcessTask) and task.spec.result_errors:
                return True
            if isinstance(task, SubgraphTask) and task.capture_error:
                return True
            if isinstance(task, BranchControl) and task.otherwise._uses_result_policy:
                return True
            if isinstance(task, (BodyTask, MapControl)) and task.body is not None and task.body._uses_result_policy:
                return True
        return False

    @cached_property
    def declared_errors(self) -> frozenset[str]:
        """Infer errors that can escape this template without being captured."""
        errors = {self.return_error[0]} if self.return_error is not None else set()
        for task in self.tasks:
            if isinstance(task, ProcessTask) and not task.capture_error:
                errors.update(task.spec.result_errors)
            elif isinstance(task, BranchControl):
                errors.update(task.body.declared_errors, task.otherwise.declared_errors)
            elif isinstance(task, LoopControl) or (isinstance(task, SubgraphTask) and not task.capture_error):
                errors.update(task.body.declared_errors)
            elif isinstance(task, MapControl) and task.body is not None:
                errors.update(task.body.declared_errors)
        return frozenset(errors)

    @property
    def task_names(self) -> tuple[str, ...]:
        """Return the placement names in declaration order."""
        return tuple(task.name for task in self.tasks)

    def task(self, name: str) -> GraphTask:
        """Return the placement with one name, or raise `KeyError`."""
        for task in self.tasks:
            if task.name == name:
                return task
        msg = f'no task named `{name}` in this graph.'
        raise KeyError(msg)

    def build_input_namespace(self) -> PortNamespace:
        """Construct process ports for the declared graph input shape."""
        namespace = _port_for_shape('inputs', self.input_shape)
        assert isinstance(namespace, PortNamespace)
        if namespace.keys() != {name.split('.')[0] for name in self.inputs}:
            expected = sorted(namespace.keys())
            received = sorted({name.split('.')[0] for name in self.inputs})
            msg = (
                'the graph boundary namespace must declare exactly the graph inputs; '
                f'expected {expected}, received {received}.'
            )
            raise GraphTypeCheckError(msg)
        return namespace

    @property
    def result_port(self) -> str:
        """Return the single output port, or `''` when there is not exactly one."""
        outputs = self.build_output_namespace()
        return next(iter(outputs)) if len(outputs) == 1 else ''

    @property
    def result_shape(self) -> Shape:
        """Return the result port contracts, or the whole outputs namespace.

        Stored ports keep types and requiredness; element contracts overlay from the
        source endpoint so nested collections survive regrouping.
        """
        namespace = self.build_output_namespace()
        selected = namespace[self.result_port] if self.result_port else namespace
        assert isinstance(selected, (InputPort, OutputPort, PortNamespace))
        base = _shape_from_port(selected)
        site = self._output_return_site()
        tree = self.outputs if site is None else site.return_outputs or {}
        source = tree[self.result_port] if self.result_port else tree
        annotated = (site or self)._tree_shape(source)
        return _overlay_element(base, annotated)

    def _tree_shape(self, source: OutputTree | dict[str, OutputTree]) -> Shape | None:
        """Return the source element contracts for one output subtree."""
        if isinstance(source, dict):
            fields: list[tuple[str, Shape]] = []
            for name, child in source.items():
                shaped = self._tree_shape(child)
                if shaped is None:
                    return None
                fields.append((name, shaped))
            return NamespaceShape(fields=tuple(fields))
        return self._endpoint_shape(source)

    def _endpoint_shape(self, endpoint: Endpoint) -> Shape | None:
        """Return the source contracts for one output endpoint, or `None` when unknown."""
        if endpoint.task is None:
            return _select_shape(self.input_shape, endpoint.port)
        try:
            task = self.task(endpoint.task)
        except KeyError:
            return None
        if isinstance(task, ProcessTask):
            return _relative_shape(task.spec.result_shape, task.spec.result_port, endpoint.port)
        if isinstance(task, InlineOperation):
            return task.result_shape if endpoint.port == task.result_port else None
        if isinstance(task, MapControl):
            mapped = task.spec.result_shape if task.spec is not None else task.body.result_shape  # type: ignore[union-attr]
            if not isinstance(mapped, LeafShape):
                return None
            collected = DataList if task.container == 'list' else DataDict
            return _relative_shape(LeafShape(types=(collected,), element=mapped), 'result', endpoint.port)
        if isinstance(task, (SubgraphTask, LoopControl)):
            return _relative_shape(task.body.result_shape, task.body.result_port, endpoint.port)
        if isinstance(task, BranchControl):
            taken = _relative_shape(task.body.result_shape, task.body.result_port, endpoint.port)
            other = _relative_shape(task.otherwise.result_shape, task.otherwise.result_port, endpoint.port)
            return merge_branch_shape(taken, other)
        return None

    def build_output_namespace(self) -> PortNamespace:
        """Return the nested outputs with their stored types.

        Outputs regroup existing nodes instead of creating data; every leaf keeps
        the stored node its task or graph input already holds.
        """
        site = self._output_return_site()
        if site is not None:
            return site.build_return_namespace()
        return self._output_namespace(self.outputs, self.output_typehints)

    def _output_return_site(self) -> GraphIR | None:
        """Return the success site that defines the output contract, if any."""
        if self.identifier is not None and self.always_returns:
            return next(self.success_returns(), None)
        return None

    def build_return_namespace(self) -> PortNamespace:
        """Return the port contract for this region's explicit success return."""
        return self._output_namespace(self.return_outputs or {}, self.return_typehints)

    def _output_namespace(self, outputs: dict[str, OutputTree], hints: dict[str, tuple[type, ...]]) -> PortNamespace:
        namespace = PortNamespace('outputs')
        for name, source in outputs.items():
            namespace[name] = self._build_output_port(name, source, hint=hints.get(name))
        return namespace

    def _build_output_port(
        self, name: str, source: OutputTree, *, hint: tuple[type, ...] | None, present: Endpoint | None = None
    ) -> OutputPort | PortNamespace:
        """Return one output leaf or namespace, preserving the stored node types.

        Outputs regroup their source nodes instead of creating data, so a leaf
        whose source accepts `None` or stays unwired is optional downstream.
        """
        if isinstance(source, (dict, OptionalOutputNamespace)):
            optional = isinstance(source, OptionalOutputNamespace)
            if isinstance(source, OptionalOutputNamespace):
                present = source.presence
                source = source.fields
            nested = PortNamespace(name, required=not optional)
            for field, child in source.items():
                nested[field] = self._build_output_port(field, child, hint=hint, present=present)
            return nested
        if source.task is None:
            ports = self.build_input_namespace()
        else:
            try:
                task = self.task(source.task)
            except KeyError as exception:
                msg = f'graph output `{name}` refers to unknown task `{source.task}`.'
                raise GraphTypeCheckError(msg) from exception
            ports = task.output_ports()
        origin = _port_at(ports, source.port)
        if isinstance(origin, PortNamespace) and source.task is not None:
            return _output_namespace_from_origin(
                name, origin, required=origin.required and _ancestry_required(ports, source.port)
            )
        if origin is None or isinstance(origin, PortNamespace):
            msg = f'graph output `{name}` must reference a declared leaf or task namespace.'
            raise GraphTypeCheckError(msg)
        valid_type = self._output_types(origin, hint) or (DataNode,)
        # A guard already represents the optionality of its source and ancestors.
        relative = source.port
        if present is not None and source.task == present.task and source.port.startswith(f'{present.port}.'):
            ancestor = _port_at(ports, present.port)
            assert isinstance(ancestor, PortNamespace)
            ports = ancestor
            relative = source.port[len(present.port) + 1 :]
        required = _output_required(origin) and _ancestry_required(ports, relative)
        return OutputPort(name, valid_type=valid_type, required=required)

    def _output_types(
        self, origin: InputPort | OutputPort, hint: tuple[type, ...] | None
    ) -> tuple[type, ...] | type | None:
        """Return the stored types of a graph output, normalizing runtime declarations."""
        if hint:
            return tuple(kind for declared in hint for kind in _infer_node_types(declared))
        if isinstance(origin, InputPort):
            kinds = origin.valid_type or ()
            if isinstance(kinds, type):
                kinds = (kinds,)
            return tuple(kind for declared in kinds for kind in _infer_node_types(declared))
        return origin.valid_type

    def predecessors(self, name: str) -> set[str]:
        """Return the tasks one placement directly depends on."""
        return {edge.source for edge in self.dependencies if edge.target == name}

    def to_dict(self) -> dict[str, t.Any]:
        """Return the graph template without live classes."""
        return {
            'tasks': [task.to_dict() for task in self.tasks],
            'dependencies': [edge.to_dict() for edge in self.dependencies],
            'inputs': {name: [list(route) for route in targets] for name, targets in self.inputs.items()},
            'outputs': {name: _dump_output_tree(source) for name, source in self.outputs.items()},
            **(
                {'return_outputs': {name: _dump_output_tree(source) for name, source in self.return_outputs.items()}}
                if self.return_outputs is not None
                else {}
            ),
            **({'return_error': list(self.return_error)} if self.return_error is not None else {}),
            **(
                {
                    'return_typehints': {
                        name: [
                            None if kind is type(None) else get_object_loader().identify_object(kind) for kind in kinds
                        ]
                        for name, kinds in self.return_typehints.items()
                    }
                }
                if self.return_typehints
                else {}
            ),
            'identifier': self.identifier,
            'version': self.version,
            'input_namespace': dump_shape(self.input_shape),
            'output_typehints': {
                name: [None if kind is type(None) else get_object_loader().identify_object(kind) for kind in kinds]
                for name, kinds in self.output_typehints.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> GraphIR:
        """Rebuild a graph template from its serialized form."""
        version = data.get('version')
        supported = (
            _GRAPH_IR_LEGACY_VERSION,
            _GRAPH_IR_VERSION,
            _GRAPH_IR_EXPRESSION_VERSION,
            _GRAPH_IR_RESULT_VERSION,
            _GRAPH_IR_OUTPUT_TREE_VERSION,
        )
        if version not in supported:
            msg = f'cannot read a graph declaration of version `{version}`; supported versions are {supported}.'
            raise GraphTypeCheckError(msg)
        try:
            boundary = load_shape(data['input_namespace'])
            tasks = tuple(GraphTask.from_dict(task) for task in data['tasks'])
        except KeyError as exception:
            msg = f'malformed graph declaration; missing key {exception}.'
            raise GraphTypeCheckError(msg) from exception
        if not isinstance(boundary, NamespaceShape):
            msg = 'the graph boundary must be a namespace.'
            raise GraphTypeCheckError(msg)
        return cls(
            input_shape=boundary,
            tasks=tasks,
            dependencies=tuple(Dependency.from_dict(edge) for edge in data.get('dependencies', ())),
            inputs={
                name: tuple(Route(*target) for target in targets) for name, targets in data.get('inputs', {}).items()
            },
            outputs={name: _load_output_tree(source) for name, source in data.get('outputs', {}).items()},
            return_outputs=(
                {name: _load_output_tree(source) for name, source in data['return_outputs'].items()}
                if 'return_outputs' in data
                else None
            ),
            return_error=(data['return_error'][0], data['return_error'][1]) if 'return_error' in data else None,
            return_typehints={
                name: tuple(type(None) if kind is None else get_object_loader().load_object(kind) for kind in kinds)
                for name, kinds in data.get('return_typehints', {}).items()
            },
            identifier=data.get('identifier'),
            version=version,
            output_typehints={
                name: tuple(type(None) if kind is None else get_object_loader().load_object(kind) for kind in kinds)
                for name, kinds in data.get('output_typehints', {}).items()
            },
        )
