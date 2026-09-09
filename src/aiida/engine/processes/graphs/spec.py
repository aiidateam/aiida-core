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

import typing as t
from dataclasses import dataclass, field

from aiida.common.loaders import get_object_loader
from aiida.engine.processes.builder import ProcessBuilder
from aiida.engine.processes.generic.ports import PortNamespace
from aiida.engine.processes.process import Process

__all__ = ('Dependency', 'Endpoint', 'ExecutorReference', 'GraphSpec', 'GraphTask', 'MapTask', 'TaskSpec')

SPEC_VERSION: str = '1.0'
"""Version of the graph declaration format, stored with every serialized spec."""

SUPPORTED_SPEC_VERSIONS: frozenset[str] = frozenset({SPEC_VERSION})
"""Versions of the declaration format that can be read back, which a stored graph is checked against."""

TASK_SPEC_VERSION: str = '1.0'
"""Version of the task declaration format, stored with every serialized spec."""

DEFINED_TASKS: dict[str, t.Any] = {}
"""Every task that has been declared in this interpreter, by the name it is referenced under.

A task is stored by its ``module:name``, which is all a daemon worker can be given. A task written in a script,
a notebook or a shell session has no importable name, so it is kept here as well and a run in the session that
declared it finds it. Submitting such a task still needs a module a worker can import.
"""

TaskKind = t.Literal['function', 'map']
"""What a task in a graph is.

A declaration is stored as provenance and read back by later versions of AiiDA, so every task says what kind it
is. The kind is what a reader dispatches on, so it separates nodes the graph treats differently rather than
executors that differ: a task running a `CalcJob` is still a `function` node, because it is still one process
submitted with its inputs.
"""


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
            raise ValueError(f'`{process}` cannot be referenced because it has no module and name.')

        return cls(module=module, name=name)

    def load(self) -> type[Process]:
        """Return the process class this reference points to.

        :raises ImportError: if the task cannot be reached from here, which is the case for one defined where it
            cannot be imported and run by a process that did not define it.
        """
        identifier = f'{self.module}:{self.name}'

        try:
            loaded: t.Any = get_object_loader().load_object(identifier)
        except ImportError as exception:
            loaded = DEFINED_TASKS.get(identifier)

            if loaded is None:
                msg = (
                    f'task `{self.name}` is defined in `{self.module}`, which cannot be imported here. A task '
                    f'runs where it was defined, so to run this one from a daemon worker, or from another '
                    f'session, define it in a module that can be imported.'
                )
                raise ImportError(msg) from exception

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
        """Return the input ports this task takes."""
        return self.process_class.spec().inputs

    @property
    def outputs(self) -> PortNamespace:
        """Return the output ports this task produces."""
        return self.process_class.spec().outputs

    def get_builder(self) -> ProcessBuilder:
        """Return a builder with which to populate the inputs of this task."""
        return self.process_class.get_builder()

    def to_dict(self) -> dict[str, t.Any]:
        return {'identifier': self.identifier, 'executor': self.executor.to_dict(), 'version': self.version}

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> TaskSpec:
        return cls(
            identifier=data['identifier'],
            executor=ExecutorReference.from_dict(data['executor']),
            version=data.get('version', TASK_SPEC_VERSION),
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
    """A dependency carrying one output of a task into one input of another."""

    source: str
    source_port: str
    target: str
    target_port: str

    def to_dict(self) -> dict[str, str]:
        return {
            'source': self.source,
            'source_port': self.source_port,
            'target': self.target,
            'target_port': self.target_port,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Dependency:
        return cls(
            source=data['source'],
            source_port=data['source_port'],
            target=data['target'],
            target_port=data['target_port'],
        )


@dataclass(frozen=True, kw_only=True)
class GraphTask:
    """A task placed in a graph, under a name, with the inputs that are given directly.

    One node runs one process, which is what makes the graph a plain dependency graph. :class:`MapTask` is the
    node that does not, and adding a kind is how a node that the graph has to treat differently arrives.
    """

    KIND: t.ClassVar[TaskKind] = 'function'

    name: str
    spec: TaskSpec
    inputs: dict[str, t.Any] = field(default_factory=dict)

    @property
    def kind(self) -> TaskKind:
        """Return what kind of node this is, which is what a reader of a stored graph dispatches on."""
        return self.KIND

    def to_dict(self) -> dict[str, t.Any]:
        return {'name': self.name, 'kind': self.KIND, 'spec': self.spec.to_dict(), 'inputs': self.inputs}

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> GraphTask:
        """Return the task a serialized declaration describes, of whichever kind it says it is.

        :param data: the declaration of one task, as written by :meth:`to_dict`.
        :raises ValueError: if the task is of a kind this version of AiiDA does not run.
        """
        kind = data.get('kind')
        node_class = TASK_KINDS.get(t.cast(str, kind))

        if node_class is None:
            supported = ', '.join(f'`{name}`' for name in sorted(TASK_KINDS))
            msg = (
                f'task `{data.get("name")}` is of kind `{kind}`, and this version of AiiDA runs tasks of kind '
                f'{supported}. A graph stored by a newer version of AiiDA has to be run with that version.'
            )
            raise ValueError(msg)

        return node_class._from_payload(data)

    @classmethod
    def _from_payload(cls, data: dict[str, t.Any]) -> GraphTask:
        """Return a node of this kind, from a declaration already known to be of this kind."""
        return cls(name=data['name'], spec=TaskSpec.from_dict(data['spec']), inputs=data.get('inputs', {}))


@dataclass(frozen=True, kw_only=True)
class MapTask(GraphTask):
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
            spec=TaskSpec.from_dict(data['spec']),
            inputs=data.get('inputs', {}),
            item_port=data['item_port'],
        )


TASK_KINDS: dict[str, type[GraphTask]] = {node_class.KIND: node_class for node_class in (GraphTask, MapTask)}
"""The node class for each kind, which is what a stored task is read back as and checked against."""


@dataclass(frozen=True)
class GraphSpec:
    """Declarative description of a graph of tasks.

    The graph is a template: it records which tasks to run, which output of one feeds which input of another, and
    which of those outputs the graph itself returns. It runs nothing, and holds no results.

    Its own inputs are named rather than filled in, so the same declaration describes every run of the graph and
    the values arrive as inputs of the process that runs it. That is what lets one graph be placed inside
    another, and what keeps a stored declaration from being a record of one particular run. Their types are not
    recorded either, since an input has the type of the ports it feeds.
    """

    tasks: tuple[GraphTask, ...]
    dependencies: tuple[Dependency, ...] = ()
    inputs: dict[str, tuple[tuple[str, str], ...]] = field(default_factory=dict)
    outputs: dict[str, Endpoint] = field(default_factory=dict)
    version: str = SPEC_VERSION

    def __post_init__(self) -> None:
        self.validate()

    @property
    def task_names(self) -> tuple[str, ...]:
        return tuple(task.name for task in self.tasks)

    def task(self, name: str) -> GraphTask:
        """Return the task placed under the given name."""
        for task in self.tasks:
            if task.name == name:
                return task
        raise KeyError(f'no task named `{name}` in this graph.')

    def predecessors(self, name: str) -> set[str]:
        """Return the names of the tasks whose outputs the given task takes."""
        return {edge.source for edge in self.dependencies if edge.target == name}

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

        :raises ValueError: if task names are not unique, a link or output refers to an unknown task or port, or the
            dependencies contain a cycle, which would leave the graph unable to start.
        """
        names = [task.name for task in self.tasks]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            raise ValueError(f'task names have to be unique, got more than one of {sorted(duplicates)}.')

        for edge in self.dependencies:
            endpoints = (
                (edge.source, edge.source_port, 'outputs'),
                (edge.target, edge.target_port, 'inputs'),
            )

            for name, port, direction in endpoints:
                if name not in names:
                    raise ValueError(f'dependency {edge} refers to unknown task `{name}`.')

                ports = getattr(self.task(name).spec, direction)

                if port not in ports and not ports.dynamic:
                    raise ValueError(
                        f'dependency {edge} refers to `{port}`, which is not a valid {direction} of `{name}`.'
                    )

        for graph_input, targets in self.inputs.items():
            for name, port in targets:
                if name not in names:
                    raise ValueError(f'input `{graph_input}` refers to unknown task `{name}`.')

                ports = self.task(name).spec.inputs

                if port not in ports and not ports.dynamic:
                    raise ValueError(f'input `{graph_input}` refers to `{port}`, which is not an input of `{name}`.')

        for output, source in self.outputs.items():
            if source.task is None:
                if source.port not in self.inputs:
                    raise ValueError(f'output `{output}` passes on `{source.port}`, which is not an input.')

                continue

            if source.task not in names:
                raise ValueError(f'output `{output}` refers to unknown task `{source.task}`.')

            outputs = self.task(source.task).spec.outputs

            if source.port not in outputs and not outputs.dynamic:
                raise ValueError(
                    f'output `{output}` refers to `{source.port}`, which is not an output of `{source.task}`.'
                )

        for task in self.tasks:
            if isinstance(task, MapTask) and task.item_port not in task.spec.inputs and not task.spec.inputs.dynamic:
                raise ValueError(
                    f'`{task.name}` maps over `{task.item_port}`, which is not an input of `{task.spec.identifier}`.'
                )

        for edge in self.dependencies:
            if isinstance(self.task(edge.source), MapTask):
                raise ValueError(
                    f'`{edge.target}` takes `{edge.target_port}` from `{edge.source}`, which runs once per item and '
                    f'so produces a result per item. Taking the results of a map into another task is not supported '
                    f'yet; a graph can return them as an output.'
                )

        self._check_acyclic()

    def _check_acyclic(self) -> None:
        """Raise if the dependencies contain a cycle, by peeling off tasks with nothing left to wait for."""
        remaining = {task.name: self.predecessors(task.name) for task in self.tasks}

        while remaining:
            free = [name for name, waiting in remaining.items() if not waiting & remaining.keys()]

            if not free:
                raise ValueError(f'the dependencies contain a cycle between {sorted(remaining)}.')

            for name in free:
                del remaining[name]

    def to_dict(self) -> dict[str, t.Any]:
        return {
            'tasks': [task.to_dict() for task in self.tasks],
            'dependencies': [edge.to_dict() for edge in self.dependencies],
            'inputs': {name: [list(target) for target in targets] for name, targets in self.inputs.items()},
            'outputs': {name: source.to_dict() for name, source in self.outputs.items()},
            'version': self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> GraphSpec:
        """Return the graph a serialized declaration describes.

        :param data: the declaration, as written by :meth:`to_dict`.
        :raises ValueError: if the declaration is of a version this version of AiiDA does not read.
        """
        version = data.get('version')

        if version not in SUPPORTED_SPEC_VERSIONS:
            supported = ', '.join(f'`{name}`' for name in sorted(SUPPORTED_SPEC_VERSIONS))
            msg = (
                f'cannot read a graph declaration of version `{version}`, this version of AiiDA reads {supported}. '
                f'A graph stored by a newer version of AiiDA has to be run with that version.'
            )
            raise ValueError(msg)

        return cls(
            tasks=tuple(GraphTask.from_dict(task) for task in data['tasks']),
            dependencies=tuple(Dependency.from_dict(edge) for edge in data.get('dependencies', [])),
            inputs={
                name: tuple((target[0], target[1]) for target in targets)
                for name, targets in data.get('inputs', {}).items()
            },
            outputs={name: Endpoint.from_dict(source) for name, source in data.get('outputs', {}).items()},
            version=version,
        )
