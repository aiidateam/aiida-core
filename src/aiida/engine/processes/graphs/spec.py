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
from dataclasses import dataclass, field

from aiida.common.loaders import get_object_loader
from aiida.engine.processes.builder import ProcessBuilder
from aiida.engine.processes.generic.ports import PortNamespace
from aiida.engine.processes.process import Process

__all__ = (
    'BodyTask',
    'BranchTask',
    'Dependency',
    'Endpoint',
    'ExecutorReference',
    'GraphSpec',
    'GraphTask',
    'LoopTask',
    'MapGraphTask',
    'MapTask',
    'ProcessTask',
    'SubgraphTask',
    'TaskSpec',
)

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

CONDITION_PORT: str = 'condition'
"""Name of the input a branch takes the value deciding it on, kept apart from the inputs of its body."""

TaskKind = t.Literal['process', 'map', 'graph', 'branch', 'loop', 'map_graph']
"""What a task in a graph is.

A declaration is stored as provenance and read back by later versions of AiiDA, so every task says what kind it
is. The kind is what a reader dispatches on, so it separates tasks the graph treats differently rather than
executors that differ: a task running a `CalcJob` is of kind `process` just as one running a process function is,
because it is still one process submitted with its inputs.
"""


def has_port(ports: PortNamespace, path: str) -> bool:
    """Return whether a namespace has a port at the given path, which may name one inside a nested namespace.

    A namespace that takes whatever it is given has every port under it, so the walk stops at the first one of
    those it reaches rather than looking for a declaration that will never be there. A path that ends on a
    namespace rather than a port has none, since one value cannot fill a namespace.

    :param path: name of a port, or names separated by dots for one inside a nested namespace.
    """
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
    head, _, rest = path.partition(PortNamespace.NAMESPACE_SEPARATOR)

    if head not in ports:
        return ports.dynamic

    port = ports[head]

    if not isinstance(port, PortNamespace):
        return False

    return has_namespace(port, rest) if rest else True


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

    def gathers(self, port: str) -> bool:
        """Return whether this task takes a result per item under the given name, which a namespace does."""
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

    def accepts(self, port: str) -> bool:
        return has_port(self.spec.inputs, port)

    def produces(self, port: str) -> bool:
        return has_port(self.spec.outputs, port)

    def gathers(self, port: str) -> bool:
        return has_namespace(self.spec.inputs, port)

    def to_dict(self) -> dict[str, t.Any]:
        return {**super().to_dict(), 'spec': self.spec.to_dict()}

    @classmethod
    def _from_payload(cls, data: dict[str, t.Any]) -> ProcessTask:
        return cls(name=data['name'], inputs=data.get('inputs', {}), spec=TaskSpec.from_dict(data['spec']))


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
        )


@dataclass(frozen=True, kw_only=True)
class BodyTask(GraphTask):
    """A task that runs a graph of its own rather than a process.

    Keeping the body a declaration of its own, rather than merging its tasks into the graph around it, is what
    lets one body be written once and run a number of times only the run itself decides.
    """

    body: GraphSpec
    """The graph to run."""

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
class BranchTask(BodyTask):
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
    def _from_payload(cls, data: dict[str, t.Any]) -> BranchTask:
        otherwise = data.get('otherwise')
        return cls(
            name=data['name'],
            inputs=data.get('inputs', {}),
            body=GraphSpec.from_dict(data['body']),
            condition_port=data.get('condition_port', CONDITION_PORT),
            otherwise=None if otherwise is None else GraphSpec.from_dict(otherwise),
        )


@dataclass(frozen=True, kw_only=True)
class LoopTask(BodyTask):
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
    def _from_payload(cls, data: dict[str, t.Any]) -> LoopTask:
        return cls(
            name=data['name'],
            inputs=data.get('inputs', {}),
            body=GraphSpec.from_dict(data['body']),
            condition_port=data.get('condition_port', CONDITION_PORT),
            max_iterations=data['max_iterations'],
        )


@dataclass(frozen=True, kw_only=True)
class MapGraphTask(BodyTask):
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
    def _from_payload(cls, data: dict[str, t.Any]) -> MapGraphTask:
        return cls(
            name=data['name'],
            inputs=data.get('inputs', {}),
            body=GraphSpec.from_dict(data['body']),
            item_port=data['item_port'],
        )


MappedTask = MapTask | MapGraphTask
"""A task that runs once per item, and so produces a result per item rather than one."""

TASK_KINDS: dict[str, type[GraphTask]] = {
    task_class.KIND: task_class
    for task_class in (ProcessTask, MapTask, SubgraphTask, BranchTask, LoopTask, MapGraphTask)
}
"""The task class for each kind, which is what a stored task is read back as and checked against."""


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

        :raises ValueError: if task names are not unique, a dependency or output refers to an unknown task or port,
            or the dependencies contain a cycle, which would leave the graph unable to start.
        """
        names = [task.name for task in self.tasks]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            raise ValueError(f'task names have to be unique, got more than one of {sorted(duplicates)}.')

        for edge in self.dependencies:
            referrer = f'dependency {edge}'
            self._check_endpoint(edge.source, edge.source_port, 'output', referrer)

            # What ran once per item arrives as a result per item, which a namespace takes and a port does not.
            if isinstance(self.task(edge.source), MappedTask):
                self._check_gathered(edge, referrer)
            else:
                self._check_endpoint(edge.target, edge.target_port, 'input', referrer)

        for graph_input, targets in self.inputs.items():
            for name, port in targets:
                self._check_endpoint(name, port, 'input', f'input `{graph_input}`')

        for output, source in self.outputs.items():
            if source.task is None:
                if source.port not in self.inputs:
                    raise ValueError(f'output `{output}` passes on `{source.port}`, which is not an input.')

                continue

            self._check_endpoint(source.task, source.port, 'output', f'output `{output}`')

        for task in self.tasks:
            if isinstance(task, MapTask) and not task.accepts(task.item_port):
                raise ValueError(
                    f'`{task.name}` maps over `{task.item_port}`, which is not an input of `{task.spec.identifier}`.'
                )

        for task in self.tasks:
            if isinstance(task, BranchTask):
                self._check_branches(task)

        for task in self.tasks:
            if isinstance(task, LoopTask):
                self._check_loop(task)

        self._check_acyclic()

    def _check_gathered(self, edge: Dependency, referrer: str) -> None:
        """Raise if what ran once per item is taken somewhere that holds one value.

        Such a task produced a result per item, gathered under the key of each, so what takes them has to be a
        namespace. A port holds one value and would be handed a collection of them.

        :raises ValueError: if there is no such task, or the results are taken into something that is not a
            namespace.
        """
        if edge.target not in self.task_names:
            raise ValueError(f'{referrer} refers to unknown task `{edge.target}`.')

        if not self.task(edge.target).gathers(edge.target_port):
            raise ValueError(
                f'`{edge.target}` takes `{edge.target_port}` from `{edge.source}`, which runs once per item and so '
                f'produces one result per item, gathered under the key of each. `{edge.target_port}` holds one '
                f'value, so it has to be a namespace to take them, or the graph can return them as an output.'
            )

    @staticmethod
    def _check_loop(task: LoopTask) -> None:
        """Raise if a loop has no way to reach its end.

        The body has to return the value the loop goes round on, since that is what ends it. Whether it takes one
        is up to it: inside a run the answer is always yes, so there is rarely anything to read.

        :raises ValueError: if the body does not return the value the loop goes round on, or may run no times.
        """
        if task.condition_port not in task.body.outputs:
            raise ValueError(
                f'`{task.name}` goes round while `{task.condition_port}` holds, so its body has to return '
                f'`{task.condition_port}`, and it returns {sorted(task.body.outputs)}. A loop goes on from what '
                f'its body returned, so the body is what decides when to stop.'
            )

        if task.max_iterations < 1:
            raise ValueError(f'`{task.name}` may run at most {task.max_iterations} times, which is never.')

    @staticmethod
    def _check_branches(task: BranchTask) -> None:
        """Raise if the two sides of a branch would leave what it takes or produces up to the run.

        :raises ValueError: if the condition shares a name with an input of a branch, or the branches produce
            different outputs, which would leave a task after them taking something that may not be there.
        """
        for branch in task.branches:
            if task.condition_port in branch.inputs:
                raise ValueError(
                    f'`{task.name}` takes its condition on `{task.condition_port}`, which a branch also takes as '
                    f'an input, so the two would arrive on one port. Rename either of them.'
                )

        if task.otherwise is not None and set(task.otherwise.outputs) != set(task.body.outputs):
            raise ValueError(
                f'`{task.name}` produces {sorted(task.body.outputs)} when its condition holds and '
                f'{sorted(task.otherwise.outputs)} when it does not, so what it produces would depend on which '
                f'branch ran. Both branches have to return the same outputs.'
            )

    def _check_endpoint(self, name: str, port: str, direction: t.Literal['input', 'output'], referrer: str) -> None:
        """Raise if a task referred to somewhere in the graph does not exist, or has no port under that name.

        :param referrer: what refers to the endpoint, which is what the error names.
        :raises ValueError: if there is no such task, or no such port on it.
        """
        if name not in self.task_names:
            raise ValueError(f'{referrer} refers to unknown task `{name}`.')

        task = self.task(name)
        known = task.accepts(port) if direction == 'input' else task.produces(port)

        if not known:
            raise ValueError(f'{referrer} refers to `{port}`, which is not an {direction} of `{name}`.')

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
