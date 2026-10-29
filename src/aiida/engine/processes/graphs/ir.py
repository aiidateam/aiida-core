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
import typing as t
from collections.abc import Container, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from functools import cached_property

from aiida.common import _callables as callables
from aiida.common.exceptions import GraphTypeCheckError, GraphValidationError
from aiida.common.lang import override
from aiida.common.loaders import get_object_loader
from aiida.engine.processes.graphs.inputs import _at, port_for_shape, prepare_graph_inputs, shape_from_port
from aiida.engine.processes.graphs.shapes import NamespaceShape, Shape, dump_shape, load_shape
from aiida.engine.processes.ports import InputPort, OutputPort, PortNamespace, _infer_node_types
from aiida.engine.processes.process import Process
from aiida.orm import Data

__all__ = (
    'BodyTask',
    'BranchControl',
    'Dependency',
    'Endpoint',
    'GraphIR',
    'GraphTask',
    'LoopControl',
    'ProcessTask',
    'Route',
    'SubgraphTask',
    'TaskIR',
)

_GRAPH_IR_VERSION: t.Final = '0.1'
_TASK_IR_VERSION: t.Final = '0.1'
CONDITION_PORT: t.Final = 'condition'
_TaskKind: t.TypeAlias = t.Literal['process', 'graph', 'branch', 'loop']


def require_version(version: object, supported: str, what: str) -> str:
    """Reject declarations whose format this implementation cannot read."""
    if version != supported:
        msg = f'cannot read a {what} declaration of version `{version}`; supported version is `{supported}`.'
        raise GraphTypeCheckError(msg)
    return supported


def port_at(ports: PortNamespace, path: str) -> InputPort | OutputPort | PortNamespace | None:
    """Find a declared path, without treating dynamic ports as known names."""
    port: t.Any = ports
    for segment in path.split('.') if path else ():
        if not isinstance(port, PortNamespace) or segment not in port:
            return None
        port = port[segment]
    return port


def reject_dynamic_inputs(ports: PortNamespace) -> None:
    """Reject dynamic scientific inputs, but permit the engine's metadata options."""
    if ports.dynamic and ports.required:
        msg = f'graph tasks require fixed inputs; namespace `{ports.name}` is dynamic.'
        raise GraphTypeCheckError(msg)
    for child in ports.values():
        if isinstance(child, PortNamespace) and not child.is_metadata and (child.required or not child.dynamic):
            reject_dynamic_inputs(child)


def input_ports_at(task: GraphTask, path: str) -> list[t.Any]:
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
    return [port for namespace in namespaces if (port := port_at(namespace, path)) is not None]


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
                msg = f'executor payload for `{self.module}:{self.name}` is corrupt: {exception}.'
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


@dataclass(frozen=True)
class TaskIR:
    """A task's executor and its static input/output contracts."""

    identifier: str
    executor: ExecutorReference
    version: str = _TASK_IR_VERSION

    @classmethod
    def from_process(cls, process: t.Callable[..., t.Any]) -> TaskIR:
        """Reference a decorated task function, a `CalcJob` subclass, or a `WorkChain` subclass."""
        module, name = process.__module__, process.__name__
        payload: str | None = None
        if module == '__main__':
            process_class = getattr(process, 'process_class', None)
            if not (isinstance(process_class, type) and issubclass(process_class, Process)):
                process_class = process if (isinstance(process, type) and issubclass(process, Process)) else None
            if process_class is not None:
                with contextlib.suppress(TypeError):
                    payload = base64.b64encode(callables.dumps(process_class)).decode('ascii')
        return cls(identifier=name, executor=ExecutorReference(module, name, payload))

    @cached_property
    def process_class(self) -> type[Process]:
        """Return the task process class loaded from its executor reference."""
        return self.executor.load()

    @property
    def inputs(self) -> PortNamespace:
        """Return the fixed input ports of the task process."""
        ports = self.process_class.spec().inputs
        reject_dynamic_inputs(ports)
        return ports

    @property
    def outputs(self) -> PortNamespace:
        """Return the static leaf output ports of the task process."""
        ports = self.process_class.spec().outputs
        if ports.dynamic or any(isinstance(port, PortNamespace) for port in ports.values()):
            msg = 'graph tasks require static leaf outputs, not dynamic outputs or output namespaces.'
            raise GraphTypeCheckError(msg)
        return ports

    @property
    def result_port(self) -> str:
        """Return the single output port, or `''` when there is not exactly one."""
        return next(iter(self.outputs)) if len(self.outputs) == 1 else ''

    @property
    def input_shape(self) -> NamespaceShape:
        """Return the fixed input contracts as nested shapes."""
        shape = shape_from_port(self.inputs)
        assert isinstance(shape, NamespaceShape)
        return shape

    @property
    def result_shape(self) -> Shape:
        """Return the result port contracts, or the whole outputs namespace."""
        selected = self.outputs[self.result_port] if self.result_port else self.outputs
        assert isinstance(selected, (InputPort, OutputPort, PortNamespace))
        return shape_from_port(selected)

    def to_dict(self) -> dict[str, t.Any]:
        """Return the task declaration without the live process class."""
        return {'identifier': self.identifier, 'executor': self.executor.to_dict(), 'version': self.version}

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> TaskIR:
        """Rebuild a task declaration from its serialized form."""
        return cls(
            identifier=data['identifier'],
            executor=ExecutorReference.from_dict(data['executor']),
            version=require_version(data.get('version'), _TASK_IR_VERSION, 'task'),
        )


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
        return cls(task=data['task'], port=data['port'])


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
        return cls(**data)


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
                assert body is not None
                return SubgraphTask(body=body, **common)
            if kind == 'branch':
                assert body is not None
                return BranchControl(
                    body=body,
                    otherwise=GraphIR.from_dict(data['otherwise']),
                    condition_port=data.get('condition_port', CONDITION_PORT),
                    **common,
                )
            if kind == 'loop':
                assert body is not None
                return LoopControl(
                    body=body,
                    condition_port=data.get('condition_port', CONDITION_PORT),
                    max_iterations=data['max_iterations'],
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

    Documented extension point for branch/loop bodies: subclass and set ``KIND``.
    Never instantiated directly.
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

    ``condition_port`` is a synthetic port wired directly into the placement inputs; validation
    rejects it from both side templates, so it never appears in their declared inputs.
    """

    KIND: t.ClassVar[_TaskKind] = 'branch'
    condition_port: str = CONDITION_PORT
    otherwise: GraphIR

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
    condition_port: str = CONDITION_PORT
    max_iterations: int = 1000

    @override
    def to_dict(self) -> dict[str, t.Any]:
        return {**super().to_dict(), 'condition_port': self.condition_port, 'max_iterations': self.max_iterations}


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
        """Return the static leaf outputs of the task process."""
        return self.spec.outputs

    @override
    def to_dict(self) -> dict[str, t.Any]:
        """Return the placement with its task declaration."""
        return {**super().to_dict(), 'spec': self.spec.to_dict()}


@dataclass(frozen=True)
class GraphIR:
    """A static graph template, with fixed input namespaces and named leaf outputs."""

    tasks: tuple[GraphTask, ...]
    input_shape: NamespaceShape
    dependencies: tuple[Dependency, ...] = ()
    inputs: dict[str, tuple[Route, ...]] = field(default_factory=dict)
    outputs: dict[str, Endpoint] = field(default_factory=dict)
    identifier: str | None = None
    version: str = _GRAPH_IR_VERSION
    output_typehints: dict[str, tuple[type, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

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
        namespace = port_for_shape('inputs', self.input_shape)
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
        return shape_from_port(selected)

    def build_output_namespace(self) -> PortNamespace:
        """Return the named leaf outputs with their stored types."""
        namespace = PortNamespace('outputs')
        for name, source in self.outputs.items():
            if source.task is None:
                origin = port_at(self.build_input_namespace(), source.port)
            else:
                try:
                    task = self.task(source.task)
                except KeyError as exception:
                    msg = f'graph output `{name}` refers to unknown task `{source.task}`.'
                    raise GraphTypeCheckError(msg) from exception
                origin = port_at(task.output_ports(), source.port)
            if origin is None or isinstance(origin, PortNamespace):
                msg = f'graph output `{name}` must reference a declared leaf.'
                raise GraphTypeCheckError(msg)
            namespace[name] = OutputPort(name, valid_type=self._output_types(name, origin) or (Data,))
        return namespace

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

    def prepare_inputs(self, inputs: Mapping[str, t.Any]) -> dict[str, t.Any]:
        """Fill graph defaults and aggregate missing inputs without storing provenance."""
        return prepare_graph_inputs(self.build_input_namespace(), inputs, self.identifier)

    def serialize_inputs(self, inputs: Mapping[str, t.Any]) -> dict[str, t.Any]:
        """Prepare the graph inputs and validate them against every consumer."""
        namespace = self.build_input_namespace()
        prepared = prepare_graph_inputs(namespace, inputs, self.identifier)
        serialized = namespace.serialize(prepared)
        if serialized is None:
            msg = 'graph inputs serialized to `None`; expected a mapping.'
            raise GraphValidationError(msg)
        runtime = namespace.prepare(serialized).runtime
        assert isinstance(runtime, Mapping)
        error = namespace.validate(runtime)
        if error is not None:
            raise GraphValidationError(error)
        for name, targets in self.inputs.items():
            try:
                value = _at(serialized, name)
            except KeyError:
                continue
            for task, path in targets:
                for port in input_ports_at(self.task(task), path):
                    error = port.validate(port.prepare(value).runtime)
                    if error is not None:
                        raise GraphValidationError(error)
        return serialized

    def predecessors(self, name: str) -> set[str]:
        """Return the tasks one placement directly depends on."""
        return {edge.source for edge in self.dependencies if edge.target == name}

    def ready(self, done: Container[str], dispatched: Container[str]) -> list[str]:
        """Return the undispatched placements whose predecessors all finished."""
        return [
            task.name
            for task in self.tasks
            if task.name not in dispatched and all(predecessor in done for predecessor in self.predecessors(task.name))
        ]

    def validate(self) -> None:
        """Check names, inputs, dependencies, regions, outputs, and acyclicity."""
        # Imported here: validation reads this module's port helpers at runtime.
        from aiida.engine.processes.graphs.validate import validate_graph

        validate_graph(self)

    def to_dict(self) -> dict[str, t.Any]:
        """Return the graph template without live classes."""
        return {
            'tasks': [task.to_dict() for task in self.tasks],
            'dependencies': [edge.to_dict() for edge in self.dependencies],
            'inputs': {name: [list(route) for route in targets] for name, targets in self.inputs.items()},
            'outputs': {name: source.to_dict() for name, source in self.outputs.items()},
            'identifier': self.identifier,
            'version': self.version,
            'input_namespace': dump_shape(self.input_shape),
            'output_typehints': {
                name: [get_object_loader().identify_object(kind) for kind in kinds]
                for name, kinds in self.output_typehints.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> GraphIR:
        """Rebuild a graph template from its serialized form."""
        version = require_version(data.get('version'), _GRAPH_IR_VERSION, 'graph')
        boundary = load_shape(data['input_namespace'])
        if not isinstance(boundary, NamespaceShape):
            msg = 'the graph boundary must be a namespace.'
            raise GraphTypeCheckError(msg)
        return cls(
            input_shape=boundary,
            tasks=tuple(GraphTask.from_dict(task) for task in data['tasks']),
            dependencies=tuple(Dependency.from_dict(edge) for edge in data.get('dependencies', ())),
            inputs={
                name: tuple(Route(*target) for target in targets) for name, targets in data.get('inputs', {}).items()
            },
            outputs={name: Endpoint.from_dict(source) for name, source in data.get('outputs', {}).items()},
            identifier=data.get('identifier'),
            version=version,
            output_typehints={
                name: tuple(get_object_loader().load_object(kind) for kind in kinds)
                for name, kinds in data.get('output_typehints', {}).items()
            },
        )
