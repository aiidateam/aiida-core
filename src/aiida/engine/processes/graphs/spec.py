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
import typing as t
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field

from aiida.common.loaders import get_object_loader
from aiida.engine.processes.graphs.inputs import at, port_for_shape, prepare_inputs, shape_from_port
from aiida.engine.processes.graphs.shapes import NamespaceShape, Shape, load_shape
from aiida.engine.processes.ports import InputPort, OutputPort, PortNamespace, infer_valid_type_from_type_annotation
from aiida.engine.processes.process import Process
from aiida.orm import Data

__all__ = (
    'BranchControl',
    'Dependency',
    'Endpoint',
    'GraphSpec',
    'LoopControl',
    'ProcessTask',
    'SubgraphTask',
    'TaskSpec',
)

SPEC_VERSION = '1.0'
TASK_SPEC_VERSION = '1.0'
CONDITION_PORT = 'condition'
TaskKind = t.Literal['process', 'graph', 'branch', 'loop']


def readable_version(version: object, supported: str, what: str) -> str:
    """Reject declarations whose format this implementation cannot read."""
    if version != supported:
        msg = f'cannot read a {what} declaration of version `{version}`; supported version is `{supported}`.'
        raise ValueError(msg)
    return supported


def port_at(ports: PortNamespace, path: str) -> InputPort | OutputPort | PortNamespace | None:
    """Find a declared path, without treating dynamic ports as known names."""
    port: t.Any = ports
    for segment in path.split('.') if path else ():
        if not isinstance(port, PortNamespace) or segment not in port:
            return None
        port = port[segment]
    return port


def fixed_inputs(ports: PortNamespace) -> None:
    """Reject dynamic scientific inputs, but permit the engine's metadata options."""
    if ports.dynamic:
        msg = f'graph tasks require fixed inputs; namespace `{ports.name}` is dynamic.'
        raise TypeError(msg)
    for child in ports.values():
        if isinstance(child, PortNamespace) and not child.is_metadata:
            fixed_inputs(child)


@dataclass(frozen=True)
class ExecutorReference:
    """The importable name of a decorated task function."""

    module: str
    name: str

    def load(self) -> type[Process]:
        loaded = get_object_loader().load_object(f'{self.module}:{self.name}')
        if getattr(loaded, 'is_process_function', False):
            return loaded.process_class
        if isinstance(loaded, type) and issubclass(loaded, Process):
            return loaded
        msg = f'`{self.module}:{self.name}` does not resolve to a task process.'
        raise ImportError(msg)

    def to_dict(self) -> dict[str, str]:
        return {'module': self.module, 'name': self.name}

    @classmethod
    def from_dict(cls, data: Mapping[str, str]) -> ExecutorReference:
        return cls(module=data['module'], name=data['name'])


@dataclass(frozen=True)
class TaskSpec:
    """A task's executor and its static input/output contracts."""

    identifier: str
    executor: ExecutorReference
    version: str = TASK_SPEC_VERSION

    @classmethod
    def from_process(cls, process: t.Any) -> TaskSpec:
        return cls(identifier=process.__name__, executor=ExecutorReference(process.__module__, process.__name__))

    @property
    def process_class(self) -> type[Process]:
        return self.executor.load()

    @property
    def inputs(self) -> PortNamespace:
        ports = self.process_class.spec().inputs
        fixed_inputs(ports)
        return ports

    @property
    def outputs(self) -> PortNamespace:
        ports = self.process_class.spec().outputs
        if ports.dynamic or any(isinstance(port, PortNamespace) for port in ports.values()):
            msg = 'graph tasks require static leaf outputs, not dynamic outputs or output namespaces.'
            raise TypeError(msg)
        return ports

    @property
    def result_port(self) -> str:
        return next(iter(self.outputs)) if len(self.outputs) == 1 else ''

    @property
    def input_shape(self) -> NamespaceShape:
        shape = shape_from_port(self.inputs, defaults=False)
        assert isinstance(shape, NamespaceShape)
        return shape

    @property
    def result_shape(self) -> Shape:
        selected = self.outputs[self.result_port] if self.result_port else self.outputs
        assert isinstance(selected, (InputPort, OutputPort, PortNamespace))
        return shape_from_port(selected, defaults=False)

    def to_dict(self) -> dict[str, t.Any]:
        return {'identifier': self.identifier, 'executor': self.executor.to_dict(), 'version': self.version}

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> TaskSpec:
        return cls(
            identifier=data['identifier'],
            executor=ExecutorReference.from_dict(data['executor']),
            version=readable_version(data.get('version'), TASK_SPEC_VERSION, 'task'),
        )


@dataclass(frozen=True)
class Endpoint:
    """A task output, or a graph input passed through unchanged."""

    port: str
    task: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {'task': self.task, 'port': self.port}

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> Endpoint:
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
            raise ValueError(msg)

    @property
    def carried_between(self) -> tuple[str, str] | None:
        if self.source_port is None or self.target_port is None:
            return None
        return self.source_port, self.target_port

    def to_dict(self) -> dict[str, str | None]:
        return {
            'source': self.source,
            'target': self.target,
            'source_port': self.source_port,
            'target_port': self.target_port,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> Dependency:
        return cls(**data)


@dataclass(frozen=True, kw_only=True)
class GraphTask(abc.ABC):
    """A named process or control-flow task with directly supplied inputs."""

    KIND: t.ClassVar[TaskKind]
    name: str
    inputs: dict[str, t.Any] = field(default_factory=dict)

    @property
    def kind(self) -> TaskKind:
        return self.KIND

    @abc.abstractmethod
    def input_ports(self) -> tuple[PortNamespace, ...]:
        """Return the contracts accepted by this placement."""

    @abc.abstractmethod
    def output_ports(self) -> PortNamespace:
        """Return the static outputs produced by this placement."""

    def to_dict(self) -> dict[str, t.Any]:
        return {'name': self.name, 'kind': self.kind, 'inputs': deepcopy(self.inputs)}

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> GraphTask:
        common = {'name': data['name'], 'inputs': data.get('inputs', {})}
        kind = data.get('kind')
        if kind == 'process':
            return ProcessTask(spec=TaskSpec.from_dict(data['spec']), **common)
        body = GraphSpec.from_dict(data['body']) if kind in ('graph', 'branch', 'loop') else None
        if kind == 'graph':
            assert body is not None
            return SubgraphTask(body=body, **common)
        if kind == 'branch':
            assert body is not None
            return BranchControl(
                body=body,
                otherwise=GraphSpec.from_dict(data['otherwise']) if data.get('otherwise') is not None else None,
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
        msg = f'unsupported graph task kind `{kind}`.'
        raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class ProcessTask(GraphTask):
    KIND: t.ClassVar[TaskKind] = 'process'
    spec: TaskSpec

    def input_ports(self) -> tuple[PortNamespace, ...]:
        return (self.spec.inputs,)

    def output_ports(self) -> PortNamespace:
        return self.spec.outputs

    def to_dict(self) -> dict[str, t.Any]:
        return {**super().to_dict(), 'spec': self.spec.to_dict()}


@dataclass(frozen=True, kw_only=True)
class BodyTask(GraphTask):
    body: GraphSpec

    def input_ports(self) -> tuple[PortNamespace, ...]:
        return (self.body.input_spec(),)

    def output_ports(self) -> PortNamespace:
        return self.body.output_spec()

    def to_dict(self) -> dict[str, t.Any]:
        return {**super().to_dict(), 'body': self.body.to_dict()}


@dataclass(frozen=True, kw_only=True)
class SubgraphTask(BodyTask):
    KIND: t.ClassVar[TaskKind] = 'graph'


@dataclass(frozen=True, kw_only=True)
class BranchControl(BodyTask):
    KIND: t.ClassVar[TaskKind] = 'branch'
    condition_port: str = CONDITION_PORT
    otherwise: GraphSpec | None = None

    @property
    def branches(self) -> tuple[GraphSpec, ...]:
        return (self.body,) if self.otherwise is None else (self.body, self.otherwise)

    def input_ports(self) -> tuple[PortNamespace, ...]:
        return tuple(branch.input_spec() for branch in self.branches)

    def to_dict(self) -> dict[str, t.Any]:
        return {
            **super().to_dict(),
            'condition_port': self.condition_port,
            'otherwise': None if self.otherwise is None else self.otherwise.to_dict(),
        }


@dataclass(frozen=True, kw_only=True)
class LoopControl(BodyTask):
    KIND: t.ClassVar[TaskKind] = 'loop'
    condition_port: str = CONDITION_PORT
    max_iterations: int = 1000

    def to_dict(self) -> dict[str, t.Any]:
        return {**super().to_dict(), 'condition_port': self.condition_port, 'max_iterations': self.max_iterations}


@dataclass(frozen=True)
class GraphSpec:
    """A static graph template, with fixed input namespaces and named leaf outputs."""

    tasks: tuple[GraphTask, ...]
    dependencies: tuple[Dependency, ...] = ()
    inputs: dict[str, tuple[tuple[str, str], ...]] = field(default_factory=dict)
    outputs: dict[str, Endpoint] = field(default_factory=dict)
    identifier: str | None = None
    version: str = SPEC_VERSION
    input_namespace: dict[str, t.Any] | None = None
    output_typehints: dict[str, tuple[type, ...]] = field(default_factory=dict)
    result_path: str | None = None

    def __post_init__(self) -> None:
        if self.input_namespace is not None:
            object.__setattr__(self, 'input_namespace', deepcopy(self.input_namespace))
        self.validate()

    @property
    def task_names(self) -> tuple[str, ...]:
        return tuple(task.name for task in self.tasks)

    def task(self, name: str) -> GraphTask:
        for task in self.tasks:
            if task.name == name:
                return task
        msg = f'no task named `{name}` in this graph.'
        raise KeyError(msg)

    def input_spec(self) -> PortNamespace:
        if self.input_namespace is not None:
            namespace = port_for_shape('inputs', load_shape(self.input_namespace))
            if not isinstance(namespace, PortNamespace) or namespace.keys() != {
                name.split('.')[0] for name in self.inputs
            }:
                msg = 'the graph boundary namespace must declare exactly the graph inputs.'
                raise ValueError(msg)
            return namespace
        namespace = PortNamespace('inputs')
        for name in self.inputs:
            if '.' in name:
                msg = f'graph input path `{name}` requires a declared namespace.'
                raise ValueError(msg)
            consumers = [
                port for task, path in self.inputs[name] for port in self._input_ports_at(self.task(task), path)
            ]
            if consumers:
                shape = shape_from_port(consumers[0], defaults=False)
                namespace[name] = port_for_shape(name, shape)
            else:
                namespace[name] = InputPort(name, valid_type=Data)
        return namespace

    @property
    def input_shape(self) -> NamespaceShape:
        shape = shape_from_port(self.input_spec())
        assert isinstance(shape, NamespaceShape)
        return shape

    @property
    def result_port(self) -> str:
        return (
            self.result_path
            if self.result_path is not None
            else next(iter(self.outputs))
            if len(self.outputs) == 1
            else ''
        )

    @property
    def result_shape(self) -> Shape:
        namespace = self.output_spec()
        selected = namespace[self.result_port] if self.result_port else namespace
        assert isinstance(selected, (InputPort, OutputPort, PortNamespace))
        return shape_from_port(selected, defaults=False)

    def output_spec(self) -> PortNamespace:
        namespace = PortNamespace('outputs')
        for name, source in self.outputs.items():
            if source.task is None:
                origin = port_at(self.input_spec(), source.port)
            else:
                origin = port_at(self.task(source.task).output_ports(), source.port)
            if origin is None or isinstance(origin, PortNamespace):
                msg = f'graph output `{name}` must reference a declared leaf.'
                raise ValueError(msg)
            hint = self.output_typehints.get(name)
            types = (
                tuple(kind for declared in hint for kind in infer_valid_type_from_type_annotation(declared))
                if hint
                else origin.valid_type
            )
            if isinstance(origin, InputPort) and not hint:
                types = tuple(
                    kind
                    for declared in (origin.valid_type or ())
                    for kind in infer_valid_type_from_type_annotation(declared)
                )
            namespace[name] = OutputPort(name, valid_type=types or (Data,))
        return namespace

    def prepare_inputs(self, inputs: Mapping[str, t.Any]) -> dict[str, t.Any]:
        return prepare_inputs(self.input_spec(), inputs, self.identifier)

    def serialize_inputs(self, inputs: Mapping[str, t.Any]) -> dict[str, t.Any]:
        namespace = self.input_spec()
        prepared = self.prepare_inputs(inputs)
        serialized = namespace.serialize(prepared)
        assert serialized is not None
        error = namespace.validate(namespace.prepare(serialized))
        if error is not None:
            raise ValueError(error)
        for name, targets in self.inputs.items():
            try:
                value = at(serialized, name)
            except KeyError:
                continue
            for task, path in targets:
                for port in self._input_ports_at(self.task(task), path):
                    error = port.validate(port.prepare(value))
                    if error is not None:
                        raise ValueError(error)
        return serialized

    @staticmethod
    def _input_ports_at(task: GraphTask, path: str) -> list[t.Any]:
        if isinstance(task, (BranchControl, LoopControl)) and path == task.condition_port:
            return []
        return [port for namespace in task.input_ports() if (port := port_at(namespace, path)) is not None]

    def predecessors(self, name: str) -> set[str]:
        return {edge.source for edge in self.dependencies if edge.target == name}

    def ready(self, done: t.Container[str], dispatched: t.Container[str]) -> list[str]:
        return [
            task.name
            for task in self.tasks
            if task.name not in dispatched and all(predecessor in done for predecessor in self.predecessors(task.name))
        ]

    @staticmethod
    def _check_types(source: t.Any, target: t.Any, context: str) -> None:
        if isinstance(source, PortNamespace) or isinstance(target, PortNamespace):
            if not isinstance(source, PortNamespace) or not isinstance(target, PortNamespace):
                msg = f'{context} has incompatible value and namespace shapes.'
                raise ValueError(msg)
            for name, child in target.items():
                if name in source:
                    GraphSpec._check_types(source[name], child, context)
                elif child.required:
                    msg = f'{context} is missing required field `{name}`.'
                    raise ValueError(msg)
            return

        def stored(port: t.Any) -> tuple[type, ...]:
            kinds = port.valid_type or ()
            kinds = (kinds,) if isinstance(kinds, type) else kinds
            return tuple(
                kind
                for declared in kinds
                if declared is not type(None)
                for kind in infer_valid_type_from_type_annotation(declared)
            )

        produced, accepted = stored(source), stored(target)
        if (
            produced
            and accepted
            and Data not in produced
            and not all(any(issubclass(kind, expected) for expected in accepted) for kind in produced)
        ):
            msg = f'{context} has incompatible types: {produced} cannot feed {accepted}.'
            raise ValueError(msg)

    def validate(self) -> None:
        if len(set(self.task_names)) != len(self.task_names):
            msg = 'task names must be unique.'
            raise ValueError(msg)
        boundary = self.input_spec()
        for name, targets in self.inputs.items():
            origin = port_at(boundary, name)
            for task_name, path in targets:
                task = self.task(task_name)
                ports = self._input_ports_at(task, path)
                if not ports and not (isinstance(task, (BranchControl, LoopControl)) and path == task.condition_port):
                    msg = f'input `{name}` refers to unknown input `{task_name}.{path}`.'
                    raise ValueError(msg)
                for target in ports:
                    self._check_types(origin, target, f'graph input `{name}`')
        for edge in self.dependencies:
            source, target = self.task(edge.source), self.task(edge.target)
            if edge.carried_between is not None:
                origin = port_at(source.output_ports(), edge.source_port or '')
                ports = self._input_ports_at(target, edge.target_port or '')
                if origin is None or isinstance(origin, PortNamespace):
                    msg = f'dependency refers to unknown output `{edge.source}.{edge.source_port}`.'
                    raise ValueError(msg)
                if not ports and not (
                    isinstance(target, (BranchControl, LoopControl)) and edge.target_port == target.condition_port
                ):
                    msg = f'dependency refers to unknown input `{edge.target}.{edge.target_port}`.'
                    raise ValueError(msg)
                for port in ports:
                    self._check_types(origin, port, f'dependency `{edge.source}` to `{edge.target}`')
        for task in self.tasks:
            task.input_ports()
            task.output_ports()
            if isinstance(task, BranchControl) and task.otherwise is not None:
                if task.condition_port in task.body.inputs or task.condition_port in task.otherwise.inputs:
                    msg = 'branch condition conflicts with a body input.'
                    raise ValueError(msg)
                if task.body.outputs.keys() != task.otherwise.outputs.keys():
                    msg = 'both branches must return the same outputs.'
                    raise ValueError(msg)
                self._check_types(task.body.output_spec(), task.otherwise.output_spec(), 'branch outputs')
                self._check_types(task.otherwise.output_spec(), task.body.output_spec(), 'branch outputs')
            if isinstance(task, LoopControl) and (
                task.condition_port not in task.body.outputs or task.max_iterations < 1
            ):
                msg = 'a loop must return its condition and allow at least one iteration.'
                raise ValueError(msg)
        self.output_spec()
        for name, endpoint in self.outputs.items():
            origin = (
                port_at(boundary, endpoint.port)
                if endpoint.task is None
                else port_at(self.task(endpoint.task).output_ports(), endpoint.port)
            )
            self._check_types(origin, self.output_spec()[name], f'graph output `{name}`')
        remaining = {name: self.predecessors(name) for name in self.task_names}
        while remaining:
            free = [name for name, waiting in remaining.items() if not waiting & remaining.keys()]
            if not free:
                msg = f'the dependencies contain a cycle between {sorted(remaining)}.'
                raise ValueError(msg)
            for name in free:
                del remaining[name]

    def to_dict(self) -> dict[str, t.Any]:
        return {
            'tasks': [task.to_dict() for task in self.tasks],
            'dependencies': [edge.to_dict() for edge in self.dependencies],
            'inputs': {name: [list(target) for target in targets] for name, targets in self.inputs.items()},
            'outputs': {name: source.to_dict() for name, source in self.outputs.items()},
            'identifier': self.identifier,
            'version': self.version,
            'input_namespace': deepcopy(self.input_namespace),
            'result_path': self.result_path,
            'output_typehints': {
                name: [get_object_loader().identify_object(kind) for kind in kinds]
                for name, kinds in self.output_typehints.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, t.Any]) -> GraphSpec:
        return cls(
            tasks=tuple(GraphTask.from_dict(task) for task in data['tasks']),
            dependencies=tuple(Dependency.from_dict(edge) for edge in data.get('dependencies', ())),
            inputs={
                name: tuple(tuple(target) for target in targets) for name, targets in data.get('inputs', {}).items()
            },
            outputs={name: Endpoint.from_dict(source) for name, source in data.get('outputs', {}).items()},
            identifier=data.get('identifier'),
            version=readable_version(data.get('version'), SPEC_VERSION, 'graph'),
            input_namespace=data.get('input_namespace'),
            result_path=data.get('result_path'),
            output_typehints={
                name: tuple(get_object_loader().load_object(kind) for kind in kinds)
                for name, kinds in data.get('output_typehints', {}).items()
            },
        )
