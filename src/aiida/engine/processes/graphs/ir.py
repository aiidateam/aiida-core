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
from dataclasses import dataclass, field
from functools import cached_property

from aiida.common import _callables as callables
from aiida.common.exceptions import GraphTypeCheckError
from aiida.common.lang import override
from aiida.common.loaders import get_object_loader
from aiida.engine.processes.exit_code import ExitCode
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
from aiida.engine.processes.graphs.shapes import LeafShape, NamespaceShape, Shape, dump_shape, load_shape
from aiida.engine.processes.ports import InputPort, OutputPort, PortNamespace, _infer_node_types
from aiida.engine.processes.process import Process
from aiida.orm import DataDict, DataList
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
    'OutputTree',
    'ProcessTask',
    'Route',
    'SubgraphTask',
    'TaskIR',
)

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


def _reject_dynamic_inputs(ports: PortNamespace) -> None:
    """Reject dynamic non-metadata inputs, but permit the engine's metadata options."""
    if ports.dynamic and ports.required:
        msg = f'graph tasks require fixed inputs; namespace `{ports.name}` is dynamic.'
        raise GraphTypeCheckError(msg)
    for child in ports.values():
        if isinstance(child, PortNamespace) and not child.is_metadata and (child.required or not child.dynamic):
            _reject_dynamic_inputs(child)


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
            closed[name] = _close_dynamic(existing, shape, port_class, location)
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
    _reject_dynamic_inputs(ports)
    return ports


def _static_outputs(process_class: type[Process], declared: NamespaceShape) -> PortNamespace:
    """Return the static output ports of a task process, rejecting dynamic namespaces."""
    ports = process_class.spec().outputs
    if declared.fields:
        ports = _close_dynamic(ports, declared, OutputPort, narrow=True)
    _reject_dynamic_outputs(ports)
    return ports


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
        """Return the fixed input contracts as nested shapes."""
        shape = _shape_from_port(self.inputs)
        assert isinstance(shape, NamespaceShape)
        return shape

    @property
    def result_shape(self) -> Shape:
        """Return the result port contracts, or the whole outputs namespace."""
        selected = self.outputs[self.result_port] if self.result_port else self.outputs
        assert isinstance(selected, (InputPort, OutputPort, PortNamespace))
        return _shape_from_port(selected)

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
            version=_require_version(data.get('version'), _TASK_IR_VERSION, 'task'),
        )


def _dump_output_tree(source: OutputTree) -> dict[str, t.Any]:
    """Serialize one output leaf or nested mapping, preserving the endpoint shape."""
    if isinstance(source, dict):
        return {'nested': {name: _dump_output_tree(child) for name, child in source.items()}}
    return source.to_dict()


def _load_output_tree(data: Mapping[str, t.Any]) -> OutputTree:
    """Rebuild one output leaf or nested mapping from its serialized form."""
    if 'nested' in data:
        nested = data['nested']
        if not isinstance(nested, Mapping):
            msg = 'malformed graph declaration; nested outputs must form a mapping.'
            raise GraphTypeCheckError(msg)
        children: Mapping[str, t.Any] = nested
        return {name: _load_output_tree(child) for name, child in children.items()}
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
                return ProcessTask(spec=TaskIR.from_dict(data['spec']), **common)
            body = GraphIR.from_dict(data['body']) if kind in ('graph', 'branch', 'loop') else None
            if kind == 'graph':
                if body is None:
                    msg = 'malformed graph task declaration; missing body.'
                    raise GraphTypeCheckError(msg)
                return SubgraphTask(body=body, **common)
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
                return MapControl(spec=mapped, body=nested, container=data['container'], **common)
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
    """A nested graph dispatched once as a child process."""

    KIND: t.ClassVar[_TaskKind] = 'graph'


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
        """Return the output contracts of the taken side, representative of both.

        Validation requires both sides to agree on output names and types, so
        either side describes the branch outputs; the taken side is used.
        """
        return self.body.build_output_namespace()

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
    """A fan-out applying one unary task or graph to every element of an owned container.

    ``collection`` is the input port receiving the ``DataList``/``DataDict`` wire; exactly one
    of ``spec`` (a unary task) or ``body`` (a unary nested graph) carries the mapped callable.
    ``container`` records the lowered collection kind, so the single ``result`` output keeps it.
    The scheduler dispatches one child per element plus a collector calculation that creates
    the result container; the graph itself only returns that existing container.
    """

    KIND: t.ClassVar[_TaskKind] = 'map'
    spec: TaskIR | None = None
    body: GraphIR | None = None
    container: t.Literal['list', 'dict'] = 'list'

    def __post_init__(self) -> None:
        """Reject maps that do not carry exactly one mapped callable of a known container kind."""
        if (self.spec is None) == (self.body is None):
            msg = 'maps carry exactly one mapped callable: a task `spec` or a nested graph `body`.'
            raise GraphTypeCheckError(msg)
        if self.container not in ('list', 'dict'):
            msg = f'maps collect `list` or `dict` containers, not `{self.container}`.'
            raise GraphTypeCheckError(msg)

    @property
    def mapped_inputs(self) -> NamespaceShape:
        """Return the input contract the mapped callable applies to each element."""
        if self.spec is not None:
            return self.spec.input_shape
        assert self.body is not None
        return self.body.input_shape

    @property
    def mapped_result_port(self) -> str:
        """Return the single output port the mapped callable produces per element."""
        if self.spec is not None:
            return self.spec.result_port
        assert self.body is not None
        return self.body.result_port

    @override
    def input_ports(self) -> tuple[PortNamespace, ...]:
        """Return the collection input accepting owned lists and mappings."""
        namespace = PortNamespace('inputs')
        namespace['collection'] = InputPort('collection', valid_type=(DataList, DataDict))
        return (namespace,)

    @override
    def output_ports(self) -> PortNamespace:
        """Return the single result container of the lowered collection kind."""
        collected = (DataList,) if self.container == 'list' else (DataDict,)
        namespace = PortNamespace('outputs')
        namespace['result'] = OutputPort('result', valid_type=collected)
        return namespace

    @override
    def to_dict(self) -> dict[str, t.Any]:
        """Return the placement with its mapped callable and container kind."""
        return {
            **super().to_dict(),
            'spec': self.spec.to_dict() if self.spec is not None else None,
            'body': self.body.to_dict() if self.body is not None else None,
            'container': self.container,
        }


@dataclass(frozen=True, kw_only=True)
class ProcessTask(GraphTask):
    """A decorated task function dispatched as one child process."""

    KIND: t.ClassVar[_TaskKind] = 'process'
    spec: TaskIR

    @override
    def input_ports(self) -> tuple[PortNamespace, ...]:
        """Return the fixed input contracts of the task process."""
        return (self.spec.inputs,)

    @override
    def output_ports(self) -> PortNamespace:
        """Return the static outputs of the task process."""
        return self.spec.outputs

    @override
    def to_dict(self) -> dict[str, t.Any]:
        """Return the placement with its task declaration."""
        return {**super().to_dict(), 'spec': self.spec.to_dict()}


OutputTree: t.TypeAlias = 'Endpoint | dict[str, OutputTree]'
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

    def __post_init__(self) -> None:
        """Reject unknown operators and operand contracts the operator cannot read."""
        if self.operation not in OPERATIONS:
            msg = f'unknown operation `{self.operation}`; expected one of {sorted(OPERATIONS)}.'
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
            )
        except KeyError as exception:
            msg = f'malformed operation task declaration; missing key {exception}.'
            raise GraphTypeCheckError(msg) from exception


def _task_contains_operation(task: GraphTask) -> bool:
    """Return whether a placement evaluates an inline operation, at any nesting depth."""
    if isinstance(task, InlineOperation):
        return True
    if isinstance(task, MapControl):
        return task.body is not None and _graph_contains_operation(task.body)
    if isinstance(task, BranchControl):
        return _graph_contains_operation(task.body) or _graph_contains_operation(task.otherwise)
    if isinstance(task, BodyTask):
        return _graph_contains_operation(task.body)
    return False


def _graph_contains_operation(graph: GraphIR) -> bool:
    """Return whether any placement of a template evaluates an inline operation."""
    return any(_task_contains_operation(task) for task in graph.tasks)


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

    def __post_init__(self) -> None:
        # Imported here: validation reads this module's port helpers at runtime.
        from aiida.engine.processes.graphs.validate import validate_graph

        validate_graph(self)
        version = _GRAPH_IR_VERSION if _graph_contains_operation(self) else _GRAPH_IR_LEGACY_VERSION
        if self.version != version:
            object.__setattr__(self, 'version', version)

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
        return next(iter(self.outputs)) if len(self.outputs) == 1 else ''

    @property
    def result_shape(self) -> Shape:
        """Return the result port contracts, or the whole outputs namespace."""
        namespace = self.build_output_namespace()
        selected = namespace[self.result_port] if self.result_port else namespace
        assert isinstance(selected, (InputPort, OutputPort, PortNamespace))
        return _shape_from_port(selected)

    def build_output_namespace(self) -> PortNamespace:
        """Return the nested outputs with their stored types.

        Outputs regroup existing nodes instead of creating data; every leaf keeps
        the stored node its task or graph input already holds.
        """
        namespace = PortNamespace('outputs')
        for name, source in self.outputs.items():
            namespace[name] = self._build_output_port(name, source, path=name)
        return namespace

    def _build_output_port(self, name: str, source: OutputTree, path: str) -> OutputPort | PortNamespace:
        """Return one output leaf or namespace, preserving the stored node types.

        Outputs regroup their source nodes instead of creating data, so a leaf
        whose source accepts `None` or stays unwired is optional downstream.
        """
        if isinstance(source, dict):
            nested = PortNamespace(name)
            for field, child in source.items():
                nested[field] = self._build_output_port(field, child, path=f'{path}.{field}')
            return nested
        if source.task is None:
            ports = self.build_input_namespace()
        else:
            try:
                task = self.task(source.task)
            except KeyError as exception:
                msg = f'graph output `{path}` refers to unknown task `{source.task}`.'
                raise GraphTypeCheckError(msg) from exception
            ports = task.output_ports()
        origin = _port_at(ports, source.port)
        if origin is None or isinstance(origin, PortNamespace):
            msg = f'graph output `{path}` must reference a declared leaf.'
            raise GraphTypeCheckError(msg)
        top = path.split('.', maxsplit=1)[0]
        valid_type = self._output_types(top, origin) or (DataNode,)
        # A required leaf under an optional namespace, such as a `Result` success, may be absent with it.
        required = _output_required(origin) and _ancestry_required(ports, source.port)
        return OutputPort(name, valid_type=valid_type, required=required)

    def _output_types(self, name: str, origin: InputPort | OutputPort) -> tuple[type, ...] | type | None:
        """Return the stored types of a graph output, normalizing runtime declarations."""
        hint = self.output_typehints.get(name)
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
        if version not in (_GRAPH_IR_VERSION, _GRAPH_IR_LEGACY_VERSION):
            msg = (
                f'cannot read a graph declaration of version `{version}`; supported versions are '
                f'`{_GRAPH_IR_LEGACY_VERSION}` and `{_GRAPH_IR_VERSION}`.'
            )
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
            identifier=data.get('identifier'),
            version=version,
            output_typehints={
                name: tuple(type(None) if kind is None else get_object_loader().load_object(kind) for kind in kinds)
                for name, kinds in data.get('output_typehints', {}).items()
            },
        )
