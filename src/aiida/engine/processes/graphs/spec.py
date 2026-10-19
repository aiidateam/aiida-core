###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declaration of a graph of tasks: what to run, and how the pieces are wired."""

from __future__ import annotations

import abc
import typing as t
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field

from aiida.common.loaders import get_object_loader
from aiida.engine.processes.builder import ProcessBuilder
from aiida.engine.processes.graphs.handlers import TaskWorkChain
from aiida.engine.processes.graphs.inputs import (
    at,
    merge_ports,
    port_for_shape,
    prepare_inputs,
    shape_from_port,
)
from aiida.engine.processes.graphs.shapes import LeafShape, ManyShape, NamespaceShape, Shape, load_shape
from aiida.engine.processes.port_model import as_dict
from aiida.engine.processes.ports import InputPort, OutputPort, PortNamespace, infer_valid_type_from_type_annotation
from aiida.engine.processes.process import Process
from aiida.orm import Data, to_aiida_type

__all__ = (
    'BodyTask',
    'BranchControl',
    'Dependency',
    'Endpoint',
    'ExecutorReference',
    'GraphSpec',
    'GraphTask',
    'LoopControl',
    'MapGraphControl',
    'MapTask',
    'ProcessTask',
    'SubgraphTask',
    'TaskSpec',
)

SPEC_VERSION: str = '1.1'
"""Version of the graph declaration format, stored with every serialized spec."""

SUPPORTED_SPEC_VERSIONS: frozenset[str] = frozenset({SPEC_VERSION})
"""Versions of the declaration format that can be read back, which a stored graph is checked against."""

TASK_SPEC_VERSION: str = '1.0'
"""Version of the task declaration format, stored with every serialized spec."""

SUPPORTED_TASK_SPEC_VERSIONS: frozenset[str] = frozenset({TASK_SPEC_VERSION})
"""Versions of the task format that can be read back, which a stored task is checked against."""

DEFINED_TASKS: dict[str, t.Any] = {}
"""Every task that has been declared in this interpreter, by the name it is referenced under.

A task is stored by its ``module:name``, which is all a daemon worker can be given. A task written in a script,
a notebook or a shell session has no importable name, so it is kept here as well and a run in the session that
declared it finds it. Submitting such a task still needs a module a worker can import.
"""

CONDITION_PORT: str = 'condition'
"""Name of the input a branch takes the value deciding it on, kept apart from the inputs of its body."""

TaskKind = t.Literal['process', 'map', 'graph', 'branch', 'loop', 'map_graph']
"""What a task in a graph is.

A declaration is stored as provenance and read back by later versions of AiiDA, so every task says what kind it
is. The kind is what a reader dispatches on, so it separates tasks the graph treats differently rather than
executors that differ: a task running a `CalcJob` is of kind `process` just as one running a process function is,
because it is still one process submitted with its inputs.
"""


def readable_version(version: t.Any, supported: frozenset[str], what: str) -> str:
    """Return the version a stored declaration says it is, refusing one that cannot be read back.

    A declaration is stored as provenance and read by later versions of AiiDA, so one written by a newer version
    is refused rather than read as though it were this one.

    :param what: what is being read, which the error names.
    :raises ValueError: if the version is not one this version of AiiDA reads.
    """
    if version not in supported:
        readable = ', '.join(f'`{name}`' for name in sorted(supported))
        msg = (
            f'cannot read a {what} declaration of version `{version}`, this version of AiiDA reads {readable}. '
            f'A {what} stored by a newer version of AiiDA has to be run with that version.'
        )
        raise ValueError(msg)

    return t.cast(str, version)


def has_port(ports: PortNamespace, path: str) -> bool:
    """Return whether a namespace has a port at the given path, which may name one inside a nested namespace.

    A namespace that takes whatever it is given has every port under it, so the walk stops at the first one of
    those it reaches rather than looking for a declaration that will never be there. A path that ends on a
    namespace rather than a port has none, since one value cannot fill a namespace.

    :param path: name of a port, or names separated by dots for one inside a nested namespace.
    """
    if not path:
        return False
    head, _, rest = path.partition(PortNamespace.NAMESPACE_SEPARATOR)

    if head not in ports:
        return ports.dynamic

    port = ports[head]

    if not rest:
        return not isinstance(port, PortNamespace)

    return has_port(port, rest) if isinstance(port, PortNamespace) else False


def has_namespace(ports: PortNamespace, path: str) -> bool:
    """Return whether a namespace has another namespace at the given path, which is what a fan-out fills.

    A namespace that takes whatever it is given takes a collection of results as readily as one value, so it
    counts as one.

    :param path: name of a namespace, or names separated by dots for one inside another.
    """
    if not path:
        return True
    head, _, rest = path.partition(PortNamespace.NAMESPACE_SEPARATOR)

    if head not in ports:
        return ports.dynamic

    port = ports[head]

    if not isinstance(port, PortNamespace):
        return False

    return has_namespace(port, rest) if rest else True


def _shape(is_port: bool, is_namespace: bool) -> t.Literal['value', 'namespace'] | None:
    """Return what a name stands for, or ``None`` where it could be either.

    A namespace that takes whatever it is given has every name under it, and any of those may itself be a
    namespace, so nothing about the shape of one is settled until a run fills it in.
    """
    if is_port == is_namespace:
        return None

    return 'namespace' if is_namespace else 'value'


def _into(namespace: PortNamespace) -> t.Callable[[t.Any], t.Any]:
    """Return what stores a value given for a graph input that feeds a namespace of ports.

    A graph input declared with a structured type names a namespace at the other end, so the fields are stored one
    by one, as the ports under that namespace store what is written into them. Storing the whole of it with
    ``to_aiida_type`` instead would make one node, which the namespace then refuses.
    """

    def store(value: t.Any) -> t.Any:
        held = as_dict(value)
        given = value if held is None else held

        if not isinstance(given, Mapping):
            return to_aiida_type(value)

        return namespace.serialize(dict(given))

    return store


def _is_a_process(loaded: t.Any) -> bool:
    """Return whether what a name resolved to is a process class or a decorated process function."""
    if loaded is None:
        return False

    return bool(getattr(loaded, 'is_process_function', False)) or (
        isinstance(loaded, type) and issubclass(loaded, Process)
    )


@dataclass(frozen=True)
class ExecutorReference:
    """Importable reference to the process that realizes a task.

    The reference is stored instead of the process class itself, so that a declaration can be written to the
    database and read back. A process function is referenced through the decorated function, since that is the
    importable name; the generated process class is recovered from it on load.
    """

    module: str
    name: str

    @classmethod
    def from_process(cls, process: t.Any) -> ExecutorReference:
        """Return the reference for a process class or a decorated process function.

        The name is recorded without checking that it can be imported, so that a task defined next to the code
        that runs it stays usable. Whether it truly is importable only matters once the reference is loaded, which
        is where a daemon worker would need it anyway.

        :param process: the process class or process function to reference.
        :raises ValueError: if the process carries no module and name to reference it by.
        """
        module = getattr(process, '__module__', None)
        name = getattr(process, '__name__', None)

        if module is None or name is None:
            msg = f'`{process}` cannot be referenced because it has no module and name.'
            raise ValueError(msg)

        return cls(module=module, name=name)

    def load(self) -> type[Process]:
        """Return the process class this reference points to.

        :raises ImportError: if the task cannot be reached from here, which is the case for one defined where it
            cannot be imported and run by a process that did not define it.
        """
        identifier = f'{self.module}:{self.name}'
        cause: ImportError | None = None

        try:
            loaded: t.Any = get_object_loader().load_object(identifier)
        except ImportError as exception:
            loaded, cause = None, exception

        # A function declared a task by a call rather than by a decorator leaves the plain function under this
        # name, since ``functools.wraps`` copied it from the function that was wrapped. The name then resolves,
        # to something that is not a process, so what was declared is looked up the same way an unimportable one is.
        if not _is_a_process(loaded):
            loaded = DEFINED_TASKS.get(identifier)

        if loaded is None:
            msg = (
                f'task `{self.name}` is defined in `{self.module}`, which cannot be imported here. A task '
                f'runs where it was defined, so to run this one from a daemon worker, or from another '
                f'session, define it in a module that can be imported.'
            )
            raise ImportError(msg) from cause

        # A process function's name resolves to the decorated function, which carries the generated process class.
        if getattr(loaded, 'is_process_function', False):
            return loaded.process_class

        return loaded

    def to_dict(self) -> dict[str, str]:
        return {'module': self.module, 'name': self.name}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> ExecutorReference:
        return cls(module=data['module'], name=data['name'])


@dataclass(frozen=True)
class TaskSpec:
    """Declarative description of a task.

    A task declares what should run, without running anything itself. The ports it takes and produces are those of
    the process that realizes it, so they are derived from the executor rather than stored alongside it, which
    keeps the declaration a small value that can be written to the database and read back.
    """

    identifier: str
    executor: ExecutorReference
    version: str = TASK_SPEC_VERSION

    @classmethod
    def from_process(cls, process: t.Any, identifier: str | None = None) -> TaskSpec:
        """Return the declaration of a task that runs the given process.

        :param process: the process class or process function that realizes the task.
        :param identifier: name of the task, which defaults to the name of the process.
        """
        reference = ExecutorReference.from_process(process)
        return cls(identifier=identifier or reference.name, executor=reference)

    @property
    def process_class(self) -> type[Process]:
        """Return the process that realizes this task."""
        return self.executor.load()

    @property
    def inputs(self) -> PortNamespace:
        """Return the input ports this task takes.

        A task that declares handlers is run by a work chain that takes those ports under a namespace of its own,
        which is where the graph puts them as it launches, so what the task takes is the same either way.
        """
        process = self.process_class
        return process.task_inputs() if issubclass(process, TaskWorkChain) else process.spec().inputs

    @property
    def outputs(self) -> PortNamespace:
        """Return the output ports this task produces."""
        return self.process_class.spec().outputs

    @property
    def result_port(self) -> str:
        """Return the declared call result path, with an empty path denoting the output namespace."""
        return self.process_class.spec().result_port

    @property
    def input_shape(self) -> NamespaceShape:
        """Return the native input contract, adapted from its executor declaration."""
        shape = shape_from_port(self.inputs, defaults=False)
        assert isinstance(shape, NamespaceShape)
        return shape

    @property
    def result_shape(self) -> Shape:
        """Return the native contract for a call result, adapted from its executor declaration."""
        ports = self.outputs
        selected = ports.get_port(self.result_port) if self.result_port else ports
        assert isinstance(selected, (InputPort, OutputPort, PortNamespace))
        return shape_from_port(selected, defaults=False)

    def get_builder(self) -> ProcessBuilder:
        """Return a builder with which to populate the inputs of this task."""
        return self.process_class.get_builder()

    def to_dict(self) -> dict[str, t.Any]:
        return {'identifier': self.identifier, 'executor': self.executor.to_dict(), 'version': self.version}

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> TaskSpec:
        """Return the task a serialized declaration describes.

        :param data: the declaration, as written by :meth:`to_dict`.
        :raises ValueError: if the declaration is of a version this version of AiiDA does not read.
        """
        return cls(
            identifier=data['identifier'],
            executor=ExecutorReference.from_dict(data['executor']),
            version=readable_version(data.get('version'), SUPPORTED_TASK_SPEC_VERSIONS, 'task'),
        )


@dataclass(frozen=True)
class Endpoint:
    """Where one output of a graph comes from.

    Usually a port of one of its tasks. A graph can also return one of its own inputs, unchanged, which is what
    ``task`` being ``None`` records: the graph passes the value on rather than producing it.
    """

    port: str
    task: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {'task': self.task, 'port': self.port}

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> Endpoint:
        return cls(task=data['task'], port=data['port'])


@dataclass(frozen=True)
class Dependency:
    """A dependency of one task on another, carrying one of its outputs into one of its inputs.

    A dependency may carry nothing, which names no ports on either end. That says only that one task runs after
    another, which is what orders a task against one it takes no value from.
    """

    source: str
    target: str
    source_port: str | None = None
    target_port: str | None = None

    @property
    def carried_between(self) -> tuple[str, str] | None:
        """Return the ports a value is carried between, or ``None`` where this only orders the two tasks."""
        if self.source_port is None or self.target_port is None:
            return None

        return self.source_port, self.target_port

    def __post_init__(self) -> None:
        if (self.source_port is None) != (self.target_port is None):
            named, missing = ('source', 'target') if self.source_port is not None else ('target', 'source')
            msg = (
                f'`{self.source}` to `{self.target}` names a {named} port and no {missing} port. A dependency '
                f'carries a value from one port to another, or it names neither and orders the two tasks.'
            )
            raise ValueError(msg)

    def to_dict(self) -> dict[str, str | None]:
        return {
            'source': self.source,
            'source_port': self.source_port,
            'target': self.target,
            'target_port': self.target_port,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> Dependency:
        return cls(
            source=t.cast(str, data['source']),
            source_port=data['source_port'],
            target=t.cast(str, data['target']),
            target_port=data['target_port'],
        )


@dataclass(frozen=True, kw_only=True)
class GraphTask(abc.ABC):
    """A task placed in a graph, under a name, with the inputs that are given directly.

    What runs a task is what its kind says, and the graph needs only the names it takes and produces to wire it to
    the tasks around it. That is what lets kinds that run something other than a single process be placed in a
    graph without the graph knowing what they run.
    """

    KIND: t.ClassVar[TaskKind]

    name: str
    inputs: dict[str, t.Any] = field(default_factory=dict)

    @property
    def kind(self) -> TaskKind:
        """Return what kind of task this is, which is what a reader of a stored graph dispatches on."""
        return self.KIND

    @abc.abstractmethod
    def accepts(self, port: str) -> bool:
        """Return whether this task takes an input under the given name."""

    @abc.abstractmethod
    def produces(self, port: str) -> bool:
        """Return whether this task produces an output under the given name."""

    @property
    @abc.abstractmethod
    def has_outputs(self) -> bool:
        """Return whether this task produces anything at all.

        A task that produces nothing is run for what it does, so nothing taking its outputs says nothing about
        whether it is wired into the graph correctly.
        """

    def takes_namespace(self, port: str) -> bool:
        """Return whether the name stands for an input namespace, which takes everything under it at once."""
        return False

    def produces_namespace(self, port: str) -> bool:
        """Return whether the name stands for an output namespace, which is passed on whole."""
        return False

    def to_dict(self) -> dict[str, t.Any]:
        return {'name': self.name, 'kind': self.KIND, 'inputs': self.inputs}

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> GraphTask:
        """Return the task a serialized declaration describes, of whichever kind it says it is.

        :param data: the declaration of one task, as written by :meth:`to_dict`.
        :raises ValueError: if the task is of a kind this version of AiiDA does not run.
        """
        kind = data.get('kind')
        task_class = TASK_KINDS.get(t.cast(str, kind))

        if task_class is None:
            supported = ', '.join(f'`{name}`' for name in sorted(TASK_KINDS))
            msg = (
                f'task `{data.get("name")}` is of kind `{kind}`, and this version of AiiDA runs tasks of kind '
                f'{supported}. A graph stored by a newer version of AiiDA has to be run with that version.'
            )
            raise ValueError(msg)

        return task_class._from_payload(data)

    @classmethod
    @abc.abstractmethod
    def _from_payload(cls, data: dict[str, t.Any]) -> GraphTask:
        """Return a task of this kind, from a declaration already known to be of this kind."""


@dataclass(frozen=True, kw_only=True)
class ProcessTask(GraphTask):
    """A task that runs one process, which is what makes the graph a plain dependency graph.

    The ports it takes and produces are those of that process, so a graph of these alone needs nothing beyond the
    declarations of the processes it wires together.
    """

    KIND: t.ClassVar[TaskKind] = 'process'

    spec: TaskSpec
    validate_inputs: bool = False
    """Check complete launch inputs before dispatch, including prepared bindings."""

    def __post_init__(self) -> None:
        candidate: object = self.validate_inputs
        if not isinstance(candidate, bool):
            msg = 'Task input-validation mode must be a boolean.'
            raise TypeError(msg)

    def accepts(self, port: str) -> bool:
        return has_port(self.spec.inputs, port)

    @property
    def has_outputs(self) -> bool:
        return bool(self.spec.outputs)

    def produces(self, port: str) -> bool:
        return has_port(self.spec.outputs, port)

    def takes_namespace(self, port: str) -> bool:
        return has_namespace(self.spec.inputs, port)

    def produces_namespace(self, port: str) -> bool:
        return has_namespace(self.spec.outputs, port)

    def to_dict(self) -> dict[str, t.Any]:
        data = {**super().to_dict(), 'spec': self.spec.to_dict()}
        if self.validate_inputs:
            data['validate_inputs'] = True
        return data

    @classmethod
    def _from_payload(cls, data: dict[str, t.Any]) -> ProcessTask:
        return cls(
            name=data['name'],
            inputs=data.get('inputs', {}),
            spec=TaskSpec.from_dict(data['spec']),
            validate_inputs=data.get('validate_inputs', False),
        )


@dataclass(frozen=True, kw_only=True)
class MapTask(ProcessTask):
    """A task run once per item of a collection that only exists while the graph runs.

    How many items there are is not known when the graph is written, so the declaration says what to map over and
    where each item goes, and the expansion into one process per item stays runtime state on the checkpoint. That
    is what keeps a stored graph a template rather than a record of one particular run.
    """

    KIND: t.ClassVar[TaskKind] = 'map'

    item_port: str
    """Input port of the task that one item of the collection is bound to on each run."""

    def to_dict(self) -> dict[str, t.Any]:
        return {**super().to_dict(), 'item_port': self.item_port}

    @classmethod
    def _from_payload(cls, data: dict[str, t.Any]) -> MapTask:
        return cls(
            name=data['name'],
            inputs=data.get('inputs', {}),
            spec=TaskSpec.from_dict(data['spec']),
            item_port=data['item_port'],
            validate_inputs=data.get('validate_inputs', False),
        )


@dataclass(frozen=True, kw_only=True)
class BodyTask(GraphTask):
    """A task that runs a graph of its own rather than a process.

    Keeping the body a declaration of its own, rather than merging its tasks into the graph around it, is what
    lets one body be written once and run a number of times only the run itself decides.
    """

    body: GraphSpec
    """The graph to run."""

    @property
    def has_outputs(self) -> bool:
        return bool(self.body.outputs)

    def produces_namespace(self, port: str) -> bool:
        return self.body.output_namespace is not None and has_namespace(self.body.output_spec(), port)

    def to_dict(self) -> dict[str, t.Any]:
        return {**super().to_dict(), 'body': self.body.to_dict()}


@dataclass(frozen=True, kw_only=True)
class SubgraphTask(BodyTask):
    """A graph placed inside another graph, run as one child process of its own.

    Its body is a declaration like any other, so what the task takes and produces are that body's inputs and
    outputs.
    """

    KIND: t.ClassVar[TaskKind] = 'graph'

    def accepts(self, port: str) -> bool:
        return port in self.body.inputs

    def produces(self, port: str) -> bool:
        return port in self.body.outputs

    @classmethod
    def _from_payload(cls, data: dict[str, t.Any]) -> SubgraphTask:
        return cls(name=data['name'], inputs=data.get('inputs', {}), body=GraphSpec.from_dict(data['body']))


@dataclass(frozen=True, kw_only=True)
class BranchControl(BodyTask):
    """One of two graphs, run depending on a value that only exists once the graph is running.

    Both branches are declared, so the declaration still describes every run and only the choice is left to the
    run. A branch that produces nothing, because the condition did not hold and there is no ``otherwise``, leaves
    everything taking one of its outputs out of the run as well.
    """

    KIND: t.ClassVar[TaskKind] = 'branch'

    condition_port: str = CONDITION_PORT
    """Input port the value deciding between the branches arrives on."""

    otherwise: GraphSpec | None = None
    """The graph to run when the condition does not hold, which produces what the body produces."""

    @property
    def branches(self) -> tuple[GraphSpec, ...]:
        """Return the graphs this task chooses between."""
        return (self.body,) if self.otherwise is None else (self.body, self.otherwise)

    def accepts(self, port: str) -> bool:
        return port == self.condition_port or any(port in branch.inputs for branch in self.branches)

    def produces(self, port: str) -> bool:
        return port in self.body.outputs

    def to_dict(self) -> dict[str, t.Any]:
        otherwise = None if self.otherwise is None else self.otherwise.to_dict()
        return {**super().to_dict(), 'condition_port': self.condition_port, 'otherwise': otherwise}

    @classmethod
    def _from_payload(cls, data: dict[str, t.Any]) -> BranchControl:
        otherwise = data.get('otherwise')
        return cls(
            name=data['name'],
            inputs=data.get('inputs', {}),
            body=GraphSpec.from_dict(data['body']),
            condition_port=data.get('condition_port', CONDITION_PORT),
            otherwise=None if otherwise is None else GraphSpec.from_dict(otherwise),
        )


@dataclass(frozen=True, kw_only=True)
class LoopControl(BodyTask):
    """A graph run again and again, on what the run before it produced, while a condition holds.

    The state the loop carries is the body's outputs: each run starts from what the one before it returned, with
    the values the loop was given standing in for whatever the body does not produce. One of those values decides
    whether to go round again, so it is both an input the body takes and an output it returns, which is what lets
    a loop be written without an edge pointing backwards.

    A loop that does not run at all, because its condition was false to begin with, produces nothing, and leaves
    everything taking one of its outputs out of the run as well.
    """

    KIND: t.ClassVar[TaskKind] = 'loop'

    condition_port: str = CONDITION_PORT
    """Name of the value deciding whether to run the body again, which the body returns.

    A loop given no value to start on runs once and asks the body from then on, so a loop meant to run needs
    nothing said here.
    """

    max_iterations: int = 1000
    """How many times the body may run before the loop gives up, so a condition that never turns false ends."""

    def accepts(self, port: str) -> bool:
        # The condition is an input of the loop whether or not the body takes one, since it is what decides
        # whether the body runs at all.
        return port == self.condition_port or port in self.body.inputs

    def produces(self, port: str) -> bool:
        return port in self.body.outputs

    def to_dict(self) -> dict[str, t.Any]:
        return {
            **super().to_dict(),
            'condition_port': self.condition_port,
            'max_iterations': self.max_iterations,
        }

    @classmethod
    def _from_payload(cls, data: dict[str, t.Any]) -> LoopControl:
        return cls(
            name=data['name'],
            inputs=data.get('inputs', {}),
            body=GraphSpec.from_dict(data['body']),
            condition_port=data.get('condition_port', CONDITION_PORT),
            max_iterations=data['max_iterations'],
        )


@dataclass(frozen=True, kw_only=True)
class MapGraphControl(BodyTask):
    """A graph run once per item of a collection that only exists while the graph runs.

    What :class:`MapTask` is to :class:`ProcessTask`, this is to :class:`SubgraphTask`: the same fan-out over a
    body rather than over a single process, which is what running a whole workflow per structure needs.
    """

    KIND: t.ClassVar[TaskKind] = 'map_graph'

    item_port: str
    """Input of the body that one item of the collection is bound to on each run."""

    def accepts(self, port: str) -> bool:
        return port in self.body.inputs

    def produces(self, port: str) -> bool:
        return port in self.body.outputs

    def to_dict(self) -> dict[str, t.Any]:
        return {**super().to_dict(), 'item_port': self.item_port}

    @classmethod
    def _from_payload(cls, data: dict[str, t.Any]) -> MapGraphControl:
        return cls(
            name=data['name'],
            inputs=data.get('inputs', {}),
            body=GraphSpec.from_dict(data['body']),
            item_port=data['item_port'],
        )


MappedTask = MapTask | MapGraphControl
"""A task that runs once per item, and so produces a result per item rather than one."""

TASK_KINDS: dict[str, type[GraphTask]] = {
    task_class.KIND: task_class
    for task_class in (ProcessTask, MapTask, SubgraphTask, BranchControl, LoopControl, MapGraphControl)
}
"""The task class for each kind, which is what a stored task is read back as and checked against."""


@dataclass(frozen=True)
class GraphSpec:
    """Declarative description of a graph of tasks.

    The graph is a template: it records which tasks to run, which output of one feeds which input of another, and
    which of those outputs the graph itself returns. It runs nothing, and holds no results.

    Its own inputs are named rather than filled in, so the same declaration describes every run of the graph and
    the values arrive as inputs of the process that runs it. That is what lets one graph be placed inside
    another, and what keeps a stored declaration from being a record of one particular run. Type hints on its
    boundaries can be checked against the ports they feed and the outputs they return.
    """

    tasks: tuple[GraphTask, ...]
    dependencies: tuple[Dependency, ...] = ()
    inputs: dict[str, tuple[tuple[str, str], ...]] = field(default_factory=dict)
    """Boundary names or declared namespace paths mapped to child input endpoints."""

    outputs: dict[str, Endpoint] = field(default_factory=dict)
    identifier: str | None = None
    version: str = SPEC_VERSION
    input_typehints: dict[str, tuple[type, ...]] = field(default_factory=dict)
    output_typehints: dict[str, tuple[type, ...]] = field(default_factory=dict)
    input_namespace: dict[str, t.Any] | None = None
    """Native boundary shape snapshot, without values or ORM identities."""

    output_namespace: dict[str, t.Any] | None = None
    """Native output shape snapshot, distinct from the output source mapping."""

    result_path: str | None = None
    """The call result path; an empty path denotes the complete output namespace."""

    def __post_init__(self) -> None:
        self.validate()
        if self.output_namespace is not None:
            object.__setattr__(self, 'output_namespace', deepcopy(self.output_namespace))
            self._validate_output_namespace()
        if self.input_namespace is not None:
            object.__setattr__(self, 'input_namespace', deepcopy(self.input_namespace))
            self.input_spec()

    @property
    def task_names(self) -> tuple[str, ...]:
        return tuple(task.name for task in self.tasks)

    def task(self, name: str) -> GraphTask:
        """Return the task placed under the given name."""
        for task in self.tasks:
            if task.name == name:
                return task
        msg = f'no task named `{name}` in this graph.'
        raise KeyError(msg)

    def input_spec(self) -> PortNamespace:
        """Reconstruct the thin input namespace, inferring routed manual inputs from task ports.

        :return: an ordinary AiiDA port namespace, not an ORM container.
        """
        if self.input_namespace is not None:
            namespace = port_for_shape('inputs', load_shape(self.input_namespace))
            if not isinstance(namespace, PortNamespace) or namespace.keys() != {
                name.split('.')[0] for name in self.inputs
            }:
                msg = 'the graph boundary namespace must declare exactly the graph inputs.'
                raise ValueError(msg)
        else:
            namespace = PortNamespace('inputs')
        for name, targets in self.inputs.items():
            if '.' in name:
                namespace.get_port(name)
                continue
            declared = t.cast(InputPort | PortNamespace | None, namespace.get(name))
            if declared is not None and (isinstance(declared, PortNamespace) or declared.valid_type):
                continue
            consumers = [
                port for task_name, path in targets for port in self._input_ports_at(self.task(task_name), path)
            ]
            inferred = merge_ports(name, consumers)
            if declared is not None:
                inferred.required = declared.required
                inferred.help = declared.help if declared.help is not None else inferred.help
                if declared.has_default():
                    inferred.default = declared.default
            namespace[name] = inferred
        return namespace

    @property
    def result_port(self) -> str:
        """Return the root for structured returns, or the sole output of a scalar graph."""
        if self.result_path is not None:
            return self.result_path
        return next(iter(self.outputs)) if self.output_namespace is None and len(self.outputs) == 1 else ''

    @property
    def input_shape(self) -> NamespaceShape:
        """Return the graph boundary contract without exposing engine port objects."""
        shape = (
            load_shape(self.input_namespace) if self.input_namespace is not None else shape_from_port(self.input_spec())
        )
        assert isinstance(shape, NamespaceShape)
        return shape

    @property
    def result_shape(self) -> Shape:
        """Return the native contract for this graph's result."""
        if self.output_namespace is not None:
            shape = load_shape(self.output_namespace)
            for segment in self.result_port.split('.') if self.result_port else ():
                assert isinstance(shape, NamespaceShape)
                shape = shape.select(segment)
            return shape
        if self.result_port:
            return LeafShape(types=self.output_typehints.get(self.result_port))
        return NamespaceShape(
            fields=tuple((name, LeafShape(types=self.output_typehints.get(name))) for name in self.outputs)
        )

    def output_spec(self) -> PortNamespace:
        """Reconstruct declared output ports, or a dynamic namespace for legacy graphs."""
        if self.output_namespace is None:
            return PortNamespace('outputs', dynamic=True)
        namespace = port_for_shape('outputs', load_shape(self.output_namespace), output=True)
        if not isinstance(namespace, PortNamespace):
            msg = 'the graph output boundary must be a port namespace.'
            raise ValueError(msg)
        return namespace

    def output_required(self, path: str) -> bool:
        """Return whether an output and every namespace containing it are required."""
        if self.output_namespace is None:
            return True
        namespace = self.output_spec()
        segments = path.split('.')
        return all(namespace.get_port('.'.join(segments[:index])).required for index in range(1, len(segments) + 1))

    def _validate_output_namespace(self) -> None:
        namespace = self.output_spec()
        for path in self.outputs:
            try:
                target = namespace.get_port(path)
            except ValueError as exception:
                msg = f'graph output `{path}` is not declared in the output namespace.'
                raise ValueError(msg) from exception
            source = self.outputs[path]
            if source.task is None:
                source_namespace = self.input_spec()
            else:
                task = self.task(source.task)
                if isinstance(task, ProcessTask):
                    source_namespace = task.spec.outputs
                elif isinstance(task, BodyTask):
                    source_namespace = task.body.output_spec()
                else:
                    continue
            try:
                origin = source_namespace.get_port(source.port)
            except ValueError:
                continue
            if source.task is not None and isinstance(self.task(source.task), MappedTask):
                assert isinstance(origin, (InputPort, OutputPort, PortNamespace))
                origin = port_for_shape(
                    'collection', ManyShape(entry=shape_from_port(origin, defaults=False)), output=True
                )
            self._check_output_ports(origin, target, path)

        def required(port: PortNamespace, prefix: str = '') -> None:
            for name, child in port.items():
                path = f'{prefix}{name}'
                if any(path == mapped or path.startswith(f'{mapped}.') for mapped in self.outputs):
                    continue
                if not child.required:
                    continue
                if isinstance(child, PortNamespace) and child:
                    required(child, f'{path}.')
                else:
                    msg = f'required graph output `{path}` has no source.'
                    raise ValueError(msg)

        required(namespace)
        self.validate_typehints()

    @classmethod
    def _check_output_ports(cls, source: t.Any, target: t.Any, path: str) -> None:
        if isinstance(source, PortNamespace) != isinstance(target, PortNamespace):
            msg = f'graph output `{path}` has incompatible value and namespace shapes.'
            raise ValueError(msg)
        if not isinstance(target, PortNamespace):
            source_types = source.valid_type or ()
            target_types = target.valid_type or ()
            source_types = source_types if isinstance(source_types, tuple) else (source_types,)
            target_types = target_types if isinstance(target_types, tuple) else (target_types,)
            if isinstance(source, InputPort):
                source_types = tuple(kind for kind in source_types if kind is not type(None))
            cls._check_types(source_types, target_types, f'graph output `{path}`')
            return
        if source.entry_port is not None and target.entry_port is not None:
            cls._check_output_ports(source.entry_port, target.entry_port, f'{path}.*')
        elif source.dynamic and target.dynamic:
            source_types = source.valid_type or ()
            target_types = target.valid_type or ()
            cls._check_types(
                source_types if isinstance(source_types, tuple) else (source_types,),
                target_types if isinstance(target_types, tuple) else (target_types,),
                f'graph output `{path}.*`',
            )
        for name, child in source.items():
            if name not in target:
                if not target.dynamic:
                    msg = f'graph output `{path}.{name}` is not declared in the output namespace.'
                    raise ValueError(msg)
                continue
            cls._check_output_ports(child, target[name], f'{path}.{name}')
        for name, child in target.items():
            if child.required and name not in source and not source.dynamic:
                msg = f'required graph output `{path}.{name}` has no source.'
                raise ValueError(msg)

    @staticmethod
    def _input_ports_at(task: GraphTask, path: str) -> list[t.Any]:
        if isinstance(task, ProcessTask):
            port: t.Any = task.spec.inputs
            for segment in path.split('.'):
                if not isinstance(port, PortNamespace) or segment not in port:
                    return []
                port = port[segment]
            return [port]
        if isinstance(task, BodyTask):
            if isinstance(task, (BranchControl, LoopControl)) and path == task.condition_port:
                return []
            bodies = task.branches if isinstance(task, BranchControl) else (task.body,)
            return [body.input_spec()[path] for body in bodies if path in body.inputs]
        return []

    def prepare_inputs(self, inputs: t.Mapping[str, t.Any]) -> dict[str, t.Any]:
        """Apply boundary defaults and report required fields before constructing launch inputs.

        :param inputs: the supplied values, left unchanged.
        :return: a normalized mapping with graph defaults applied.
        """
        return prepare_inputs(self.input_spec(), inputs, self.identifier)

    def serialize_inputs(self, inputs: t.Mapping[str, t.Any]) -> dict[str, t.Any]:
        """Prepare and serialize thin namespaces as mappings of data-node leaves.

        :param inputs: supplied graph values, left unchanged.
        :return: values suitable for process input links, without a namespace node.
        """
        prepared = self.prepare_inputs(inputs)
        serialized = {
            name: value if value is None or isinstance(value, Data) else self.serializer_for_input(name)(value)
            for name, value in prepared.items()
        }
        namespace = self.input_spec()
        error = namespace.validate(namespace.prepare(serialized))
        if error is not None:
            raise ValueError(error)
        for name, targets in self.inputs.items():
            try:
                value = at(serialized, name)
            except KeyError:
                continue
            for task_name, path in targets:
                for port in self._input_ports_at(self.task(task_name), path):
                    error = port.validate(port.prepare(value))
                    if error is not None:
                        raise ValueError(error)
        return serialized

    def serializer_for_input(self, name: str) -> t.Callable[[t.Any], t.Any]:
        """Return what stores a value given for one of the graph's own inputs.

        An input has no type of its own: it has the type of the ports it feeds, so it is stored the way the port
        at the other end stores what is written into it. Without that, every input would be stored by
        ``to_aiida_type`` alone, which knows only the value it is handed, so an enum member would arrive as the
        string it prints as and a port asking for the enum would refuse it.

        :param name: the input of this graph a value was given for.
        :return: what to store it with, which is ``to_aiida_type`` where nothing more specific is known.
        """
        for task_name, port in self.inputs.get(name, ()):
            found = self._serializer_at(task_name, port)

            if found is not None:
                return found

        if self.input_namespace is not None:
            boundary = t.cast(InputPort | PortNamespace, self.input_spec()[name])
            return _into(boundary) if isinstance(boundary, PortNamespace) else boundary.serialize
        return to_aiida_type

    def _serializer_at(self, task_name: str, port: str) -> t.Callable[[t.Any], t.Any] | None:
        """Return what the named port of the named task stores what is written into it with.

        :return: the serializer, or ``None`` where this graph cannot say, which a namespace and a task holding a
            graph of its own both are.
        """
        task = self.task(task_name)

        if isinstance(task, BodyTask):
            # The port belongs to the graph inside, whose inputs carry the same names.
            return next(
                (
                    found
                    for inner_task, inner_port in task.body.inputs.get(port, ())
                    if (found := task.body._serializer_at(inner_task, inner_port)) is not None
                ),
                None,
            )

        if not isinstance(task, ProcessTask):
            return None

        holder: t.Any = task.spec.process_class.spec().inputs

        for segment in port.split('.'):
            if not isinstance(holder, PortNamespace) or segment not in holder:
                return None

            holder = holder[segment]

        if isinstance(holder, PortNamespace):
            return _into(holder)

        if isinstance(holder, InputPort) and (holder.non_db or holder.is_metadata):
            return holder.serialize
        return getattr(holder, 'serializer', None)

    @staticmethod
    def _port_types(ports: PortNamespace, path: str) -> tuple[type, ...]:
        """Return the accepted types of a declared port, or empty for a dynamic or untyped port."""
        holder: t.Any = ports
        for segment in path.split('.'):
            if not isinstance(holder, PortNamespace) or segment not in holder:
                return ()
            holder = holder[segment]
        valid = getattr(holder, 'valid_type', None)
        if valid is None:
            return ()
        types = valid if isinstance(valid, tuple) else (valid,)
        # Optional input ports accept None during parsing, not as a produced data node.
        if isinstance(holder, InputPort):
            types = tuple(kind for kind in types if kind is not type(None))
        return types

    def _types_at(self, task: GraphTask, port: str, *, output: bool) -> tuple[type, ...]:
        """Find types at a task boundary, following nested graph boundaries where necessary."""
        if isinstance(task, ProcessTask):
            return self._port_types(task.spec.outputs if output else task.spec.inputs, port)
        if isinstance(task, BodyTask):
            if isinstance(task, (BranchControl, LoopControl)) and port == task.condition_port and not output:
                return ()
            if output:
                return task.body._output_types(port)
            if isinstance(task, BranchControl):
                hints = [branch._input_types(port) for branch in task.branches if port in branch.inputs]
                return next((hint for hint in hints if hint), ())
            return task.body._input_types(port)
        return ()

    def _input_types(self, name: str) -> tuple[type, ...]:
        if '.' in name:
            return self._port_types(self.input_spec(), name)
        if name in self.input_typehints:
            return self.input_typehints[name]
        for task_name, port in self.inputs.get(name, ()):
            if hint := self._types_at(self.task(task_name), port, output=False):
                return hint
        return ()

    def _output_types(self, name: str) -> tuple[type, ...]:
        if self.output_namespace is not None:
            return self._port_types(self.output_spec(), name)
        if name in self.output_typehints:
            return self.output_typehints[name]
        source = self.outputs[name]
        if source.task is None:
            return self._input_types(source.port)
        return self._types_at(self.task(source.task), source.port, output=True)

    @staticmethod
    def _check_types(source: tuple[type, ...], target: tuple[type, ...], context: str) -> None:
        """Check that every possible source type is accepted by the target when both are known."""
        stored_source = tuple(
            (infer_valid_type_from_type_annotation(kind, stored=True) or (kind,))[0] for kind in source
        )
        stored_target = tuple(
            (infer_valid_type_from_type_annotation(kind, stored=True) or (kind,))[0] for kind in target
        )
        if (
            stored_source
            and stored_target
            and Data not in stored_source
            and not all(any(issubclass(kind, expected) for expected in stored_target) for kind in stored_source)
        ):
            msg = f'{context} has incompatible types: {source} cannot feed {target}.'
            raise ValueError(msg)

    def validate_typehints(self) -> None:
        """Validate known types at graph inputs, dependencies and outputs, including nested graphs.

        An untyped or dynamic port cannot be checked statically and is left to runtime validation.

        :raises ValueError: if a known output type cannot be accepted by an input or graph boundary.
        """
        for task in self.tasks:
            if isinstance(task, BodyTask):
                task.body.validate_typehints()
                if isinstance(task, BranchControl) and task.otherwise is not None:
                    task.otherwise.validate_typehints()
                    for name in task.body.outputs:
                        self._check_types(
                            task.otherwise._output_types(name),
                            task.body._output_types(name),
                            f'branches of `{task.name}` output `{name}`',
                        )
                        self._check_types(
                            task.body._output_types(name),
                            task.otherwise._output_types(name),
                            f'branches of `{task.name}` output `{name}`',
                        )

        for name, targets in self.inputs.items():
            types = self._input_types(name)
            for task_name, port in targets:
                task = self.task(task_name)
                if isinstance(task, MappedTask) and port == task.item_port:
                    continue
                expected = self._types_at(task, port, output=False)
                self._check_types(types, expected, f'graph input `{name}` to `{task_name}.{port}`')
                if name not in self.input_typehints and '.' not in name:
                    self._check_types(expected, types, f'graph input `{name}` to `{task_name}.{port}`')

        for edge in self.dependencies:
            if edge.carried_between is None or isinstance(self.task(edge.source), MappedTask):
                continue
            source_port, target_port = edge.carried_between
            self._check_types(
                self._types_at(self.task(edge.source), source_port, output=True),
                self._types_at(self.task(edge.target), target_port, output=False),
                f'dependency `{edge.source}.{source_port}` to `{edge.target}.{target_port}`',
            )

        for name in self.outputs:
            if name not in self.output_typehints and self.output_namespace is None:
                continue
            source = self.outputs[name]
            produced = (
                self._input_types(source.port)
                if source.task is None
                else self._types_at(self.task(source.task), source.port, output=True)
            )
            expected = (
                self._port_types(self.output_spec(), name)
                if self.output_namespace is not None
                else self.output_typehints[name]
            )
            self._check_types(produced, expected, f'graph output `{name}`')

    def predecessors(self, name: str) -> set[str]:
        """Return the names of the tasks the given one waits for, whether it takes a value from them or not."""
        return {edge.source for edge in self.dependencies if edge.target == name}

    @property
    def unread(self) -> tuple[str, ...]:
        """Return the tasks that produce something nothing looks at, in the order they were declared.

        Such a task runs, since it was declared, and runs beside whatever was meant to wait for it, which is
        what a forgotten ``after`` or a forgotten wiring of an output looks like from here.

        A task that produces nothing is left out: it is run for what it does.
        """
        waited_on = {edge.source for edge in self.dependencies}
        returned = {source.task for source in self.outputs.values() if source.task is not None}
        read = waited_on | returned

        return tuple(task.name for task in self.tasks if task.has_outputs and task.name not in read)

    def ready(self, done: t.Container[str], dispatched: t.Container[str]) -> list[str]:
        """Return the tasks whose predecessors have all finished and that have not been dispatched yet.

        :param done: names of the tasks that have finished.
        :param dispatched: names of the tasks that have been dispatched already.
        """
        return [
            task.name
            for task in self.tasks
            if task.name not in dispatched and all(predecessor in done for predecessor in self.predecessors(task.name))
        ]

    def validate(self) -> None:
        """Check that the graph is well formed.

        :raises ValueError: if task names are not unique, a dependency or output refers to an unknown task or port,
            or the dependencies contain a cycle, which would leave the graph unable to start.
        """
        names = [task.name for task in self.tasks]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            msg = f'task names have to be unique, got more than one of {sorted(duplicates)}.'
            raise ValueError(msg)

        for edge in self.dependencies:
            referrer = f'dependency {edge}'
            carried = edge.carried_between

            if carried is None:
                self._check_order(edge, referrer)
                continue

            source_port, target_port = carried
            self._check_endpoint(edge.source, source_port, 'output', referrer)

            # What ran once per item arrives as a result per item, which a namespace takes and a port does not.
            if isinstance(self.task(edge.source), MappedTask):
                self._check_gathered(edge, target_port, referrer)
            else:
                self._check_endpoint(edge.target, target_port, 'input', referrer)
                self._check_shapes_match(edge, source_port, target_port, referrer)

        for graph_input, targets in self.inputs.items():
            if '.' in graph_input:
                self.input_spec().get_port(graph_input)
            for name, port in targets:
                self._check_endpoint(name, port, 'input', f'input `{graph_input}`')

        for output, source in self.outputs.items():
            if source.task is None:
                if source.port.split('.')[0] not in self.inputs:
                    msg = f'output `{output}` passes on `{source.port}`, which is not an input.'
                    raise ValueError(msg)

                continue

            self._check_endpoint(source.task, source.port, 'output', f'output `{output}`')

        for task in self.tasks:
            if isinstance(task, MapTask) and not task.accepts(task.item_port):
                msg = f'`{task.name}` maps over `{task.item_port}`, which is not an input of `{task.spec.identifier}`.'
                raise ValueError(msg)

        for task in self.tasks:
            if isinstance(task, BranchControl):
                self._check_branches(task)

        for task in self.tasks:
            if isinstance(task, LoopControl):
                self._check_loop(task)

        self._check_acyclic()

    def _check_order(self, edge: Dependency, referrer: str) -> None:
        """Raise if a dependency that only orders two tasks names one that is not in the graph.

        :raises ValueError: if either end is unknown.
        """
        for name in (edge.source, edge.target):
            if name not in self.task_names:
                msg = f'{referrer} refers to unknown task `{name}`.'
                raise ValueError(msg)

    def _check_shapes_match(self, edge: Dependency, source_port: str, target_port: str, referrer: str) -> None:
        """Raise if one end of a dependency is a namespace and the other holds a single value.

        A namespace can be passed on whole, which is the only way to carry outputs whose names are not known
        until the task has run. What it is passed to has to be a namespace as well, since a port takes one value.

        :raises ValueError: if the two ends are of different shapes.
        """
        source, target = self.task(edge.source), self.task(edge.target)
        produces = _shape(source.produces(source_port), source.produces_namespace(source_port))
        takes = _shape(target.accepts(target_port), target.takes_namespace(target_port))

        if produces is None or takes is None or produces == takes:
            return

        namespace, other = (edge.source, edge.target) if produces == 'namespace' else (edge.target, edge.source)
        under, single = (source_port, target_port) if produces == 'namespace' else (target_port, source_port)

        msg = (
            f'{referrer} wires `{under}` of `{namespace}`, which is a namespace, onto `{single}` of `{other}`, '
            f'which holds one value. Name a port inside the namespace, or wire it onto a namespace.'
        )
        raise ValueError(msg)

    def _check_gathered(self, edge: Dependency, target_port: str, referrer: str) -> None:
        """Raise if what ran once per item is taken somewhere that holds one value.

        Such a task produced a result per item, gathered under the key of each, so what takes them has to be a
        namespace. A port holds one value and would be handed a collection of them.

        :raises ValueError: if there is no such task, or the results are taken into something that is not a
            namespace.
        """
        if edge.target not in self.task_names:
            msg = f'{referrer} refers to unknown task `{edge.target}`.'
            raise ValueError(msg)

        if not self.task(edge.target).takes_namespace(target_port):
            msg = (
                f'`{edge.target}` takes `{target_port}` from `{edge.source}`, which runs once per item and so '
                f'produces one result per item, gathered under the key of each. `{target_port}` holds one '
                f'value, so it has to be a namespace to take them, or the graph can return them as an output.'
            )
            raise ValueError(msg)

    @staticmethod
    def _check_loop(task: LoopControl) -> None:
        """Raise if a loop has no way to reach its end.

        The body has to return the value the loop goes round on, since that is what ends it. Whether it takes one
        is up to it: inside a run the answer is always yes, so there is rarely anything to read.

        :raises ValueError: if the body does not return the value the loop goes round on, or may run no times.
        """
        if task.condition_port not in task.body.outputs:
            msg = (
                f'`{task.name}` goes round while `{task.condition_port}` holds, so its body has to return '
                f'`{task.condition_port}`, and it returns {sorted(task.body.outputs)}. A loop goes on from what '
                f'its body returned, so the body is what decides when to stop.'
            )
            raise ValueError(msg)

        if task.max_iterations < 1:
            msg = f'`{task.name}` may run at most {task.max_iterations} times, which is never.'
            raise ValueError(msg)

    @staticmethod
    def _check_branches(task: BranchControl) -> None:
        """Raise if the two sides of a branch would leave what it takes or produces up to the run.

        :raises ValueError: if the condition shares a name with an input of a branch, or the branches produce
            different outputs, which would leave a task after them taking something that may not be there.
        """
        for branch in task.branches:
            if task.condition_port in branch.inputs:
                msg = (
                    f'`{task.name}` takes its condition on `{task.condition_port}`, which a branch also takes as '
                    f'an input, so the two would arrive on one port. Rename either of them.'
                )
                raise ValueError(msg)

        if task.otherwise is not None and set(task.otherwise.outputs) != set(task.body.outputs):
            msg = (
                f'`{task.name}` produces {sorted(task.body.outputs)} when its condition holds and '
                f'{sorted(task.otherwise.outputs)} when it does not, so what it produces would depend on which '
                f'branch ran. Both branches have to return the same outputs.'
            )
            raise ValueError(msg)

        if task.otherwise is not None and all(branch.output_namespace is not None for branch in task.branches):

            def contract(port: PortNamespace | OutputPort) -> tuple[t.Any, ...]:
                valid_types = port.valid_type or ()
                valid_types = valid_types if isinstance(valid_types, tuple) else (valid_types,)
                properties = (port.required, frozenset(valid_types))
                if isinstance(port, PortNamespace):
                    return (*properties, port.dynamic, {name: contract(child) for name, child in port.items()})
                return properties

            if contract(task.body.output_spec()) != contract(task.otherwise.output_spec()):
                msg = f'`{task.name}` branches have incompatible output contracts.'
                raise ValueError(msg)

    def _check_endpoint(self, name: str, port: str, direction: t.Literal['input', 'output'], referrer: str) -> None:
        """Raise if a task referred to somewhere in the graph does not exist, or has no port under that name.

        :param referrer: what refers to the endpoint, which is what the error names.
        :raises ValueError: if there is no such task, or no such port on it.
        """
        if name not in self.task_names:
            msg = f'{referrer} refers to unknown task `{name}`.'
            raise ValueError(msg)

        task = self.task(name)

        if direction == 'input':
            known = task.accepts(port) or task.takes_namespace(port)
        else:
            known = task.produces(port) or task.produces_namespace(port)

        if not known:
            msg = f'{referrer} refers to `{port}`, which is not an {direction} of `{name}`.'
            raise ValueError(msg)

    def _check_acyclic(self) -> None:
        """Raise if the dependencies contain a cycle, by peeling off tasks with nothing left to wait for."""
        remaining = {task.name: self.predecessors(task.name) for task in self.tasks}

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
            'output_namespace': deepcopy(self.output_namespace),
            'result_path': self.result_path,
            'input_typehints': {
                name: [get_object_loader().identify_object(kind) for kind in types]
                for name, types in self.input_typehints.items()
            },
            'output_typehints': {
                name: [get_object_loader().identify_object(kind) for kind in types]
                for name, types in self.output_typehints.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> GraphSpec:
        """Return the graph a serialized declaration describes.

        :param data: the declaration, as written by :meth:`to_dict`.
        :raises ValueError: if the declaration is of a version this version of AiiDA does not read.
        """
        version = readable_version(data.get('version'), SUPPORTED_SPEC_VERSIONS, 'graph')

        return cls(
            tasks=tuple(GraphTask.from_dict(task) for task in data['tasks']),
            dependencies=tuple(Dependency.from_dict(edge) for edge in data.get('dependencies', [])),
            inputs={
                name: tuple((target[0], target[1]) for target in targets)
                for name, targets in data.get('inputs', {}).items()
            },
            outputs={name: Endpoint.from_dict(source) for name, source in data.get('outputs', {}).items()},
            identifier=data.get('identifier'),
            version=version,
            input_namespace=data.get('input_namespace'),
            output_namespace=data.get('output_namespace'),
            result_path=data.get('result_path'),
            input_typehints={
                name: tuple(get_object_loader().load_object(kind) for kind in types)
                for name, types in data.get('input_typehints', {}).items()
            },
            output_typehints={
                name: tuple(get_object_loader().load_object(kind) for kind in types)
                for name, types in data.get('output_typehints', {}).items()
            },
        )
