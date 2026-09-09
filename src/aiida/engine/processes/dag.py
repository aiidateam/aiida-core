###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declaration and execution of a graph of tasks."""

from __future__ import annotations

import functools
import typing as t
from collections.abc import MutableMapping
from dataclasses import dataclass, field

from aiida.common.lang import override
from aiida.common.processes import ProcessState
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.process import Process
from aiida.engine.processes.process_spec import ProcessSpec
from aiida.engine.processes.states import Wait
from aiida.engine.processes.task import TaskSpec
from aiida.orm import Dict, List, WorkChainNode, load_node

__all__ = ('Dependency', 'Endpoint', 'GraphProcess', 'GraphSpec', 'GraphTask', 'MapTask')

SPEC_VERSION: str = '1.0'
"""Version of the graph declaration format, stored with every serialized spec."""

SUPPORTED_SPEC_VERSIONS: frozenset[str] = frozenset({SPEC_VERSION})
"""Versions of the declaration format that can be read back, which a stored graph is checked against."""

TaskKind = t.Literal['function', 'map']
"""What a task in a graph is.

A declaration is stored as provenance and read back by later versions of AiiDA, so every task says what kind it
is. The kind is what a reader dispatches on, so it separates nodes the graph treats differently rather than
executors that differ: a task running a `CalcJob` is still a `function` node, because it is still one process
submitted with its inputs.
"""


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


def _map_items(collection: t.Any, task: MapTask) -> dict[str, t.Any]:
    """Return the items a map runs over, by the key each of its results is gathered under.

    :param collection: what the task maps over, as a list or a dictionary, stored or plain.
    :param task: the task being expanded, named in the errors.
    :raises ValueError: if the collection is of a type that cannot be mapped over, or is keyed by something that
        cannot name a result.
    """
    if isinstance(collection, List):
        collection = collection.get_list()
    elif isinstance(collection, Dict):
        collection = collection.get_dict()

    if isinstance(collection, (list, tuple)):
        return {f'item_{index}': value for index, value in enumerate(collection)}

    if not isinstance(collection, dict):
        msg = (
            f'`{task.name}` maps over `{task.item_port}`, which has to be a list or a dictionary (or the `List` '
            f'or `Dict` node of one), got `{type(collection).__name__}`.'
        )
        raise ValueError(msg)

    unusable = sorted(key for key in collection if not str(key).isidentifier())

    if unusable:
        msg = (
            f'`{task.name}` maps over a dictionary keyed by {unusable}, and each result is stored under its key, '
            f'so the keys have to be usable as names.'
        )
        raise ValueError(msg)

    return dict(collection)


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
    links: tuple[Dependency, ...] = ()
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
        return {link.source for link in self.links if link.target == name}

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
            links contain a cycle, which would leave the graph unable to start.
        """
        names = [task.name for task in self.tasks]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            raise ValueError(f'task names have to be unique, got more than one of {sorted(duplicates)}.')

        for link in self.links:
            endpoints = (
                (link.source, link.source_port, 'outputs'),
                (link.target, link.target_port, 'inputs'),
            )

            for name, port, direction in endpoints:
                if name not in names:
                    raise ValueError(f'link {link} refers to unknown task `{name}`.')

                ports = getattr(self.task(name).spec, direction)

                if port not in ports and not ports.dynamic:
                    raise ValueError(f'link {link} refers to `{port}`, which is not a valid {direction} of `{name}`.')

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

        for link in self.links:
            if isinstance(self.task(link.source), MapTask):
                raise ValueError(
                    f'`{link.target}` takes `{link.target_port}` from `{link.source}`, which runs once per item and '
                    f'so produces a result per item. Taking the results of a map into another task is not supported '
                    f'yet; a graph can return them as an output.'
                )

        self._check_acyclic()

    def _check_acyclic(self) -> None:
        """Raise if the links contain a cycle, by peeling off tasks that have nothing left to wait for."""
        remaining = {task.name: self.predecessors(task.name) for task in self.tasks}

        while remaining:
            free = [name for name, waiting in remaining.items() if not waiting & remaining.keys()]

            if not free:
                raise ValueError(f'the links contain a cycle between {sorted(remaining)}.')

            for name in free:
                del remaining[name]

    def to_dict(self) -> dict[str, t.Any]:
        return {
            'tasks': [task.to_dict() for task in self.tasks],
            'links': [link.to_dict() for link in self.links],
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
            links=tuple(Dependency.from_dict(link) for link in data.get('links', [])),
            inputs={
                name: tuple((target[0], target[1]) for target in targets)
                for name, targets in data.get('inputs', {}).items()
            },
            outputs={name: Endpoint.from_dict(source) for name, source in data.get('outputs', {}).items()},
            version=version,
        )


class GraphProcess(Process):
    """Run a graph of tasks, dispatching each as a child process.

    Every task that is ready is submitted, so it is a process in its own right: it gets its own node, its own entry
    in the provenance graph under the name the graph gave it, and it is scheduled like any other process. The graph
    keeps only the bookkeeping of what it dispatched and what has finished, which travels with its checkpoint.
    """

    _node_class = WorkChainNode

    _DAG = 'dag'
    _GRAPH_INPUTS = 'graph_inputs'

    @classmethod
    def define(cls, spec: ProcessSpec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input(cls._DAG, valid_type=Dict, help='The declaration of the graph to run.')
        spec.input_namespace(
            cls._GRAPH_INPUTS,
            dynamic=True,
            required=False,
            help='The inputs the graph declares, which are passed on to the tasks that take them.',
        )
        spec.outputs.dynamic = True
        spec.exit_code(400, 'ERROR_TASK_FAILED', message='The task `{task}` did not finish successfully.')

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self._dag: GraphSpec | None = None
        # What each task dispatched, which is one process for most tasks and one per item for a map. The processes
        # are tracked under an instance name, so a task that fans out needs no second kind of bookkeeping.
        self._instances: dict[str, list[str]] = {}
        self._dispatched: dict[str, int] = {}
        self._done: dict[str, int] = {}

    @property
    def dag(self) -> GraphSpec:
        """Return the declaration of the graph being run."""
        if self._dag is None:
            self._dag = GraphSpec.from_dict(self.inputs[self._DAG].get_dict())
        return self._dag

    @override
    def save_instance_state(self, out_state: MutableMapping[str, t.Any], save_context: t.Any) -> None:
        super().save_instance_state(out_state, save_context)
        out_state['instances'] = {name: list(instances) for name, instances in self._instances.items()}
        out_state['dispatched'] = dict(self._dispatched)
        out_state['done'] = dict(self._done)

    @override
    def load_instance_state(self, saved_state: MutableMapping[str, t.Any], load_context: t.Any) -> None:
        super().load_instance_state(saved_state, load_context)
        self._dag = None
        self._instances = {name: list(instances) for name, instances in saved_state.get('instances', {}).items()}
        self._dispatched = dict(saved_state.get('dispatched', {}))
        self._done = dict(saved_state.get('done', {}))

    @override
    async def run(self) -> t.Any:
        return self._do_step()

    def _do_step(self) -> t.Any:
        """Dispatch the tasks that are ready, and wait until something finishes."""
        for name in self.dag.ready(self._succeeded, self._instances):
            self._dispatch(name)

        if self._pending:
            return Wait(self._do_step, 'waiting for dispatched tasks')

        return self._finish()

    @property
    def _pending(self) -> dict[str, int]:
        """Return the processes that have been dispatched but have not finished."""
        return {instance: pk for instance, pk in self._dispatched.items() if instance not in self._done}

    @property
    def _finished(self) -> set[str]:
        """Return the tasks all of whose processes have finished, however they finished."""
        return {
            name for name, instances in self._instances.items() if all(instance in self._done for instance in instances)
        }

    @property
    def _succeeded(self) -> set[str]:
        """Return the tasks that finished successfully, which are the only ones a next task can take inputs from.

        A task that fanned out counts as successful once every one of its processes did, so one failed item stops
        what comes after it just as a single failed task does.
        """
        return {
            name
            for name in self._finished
            if all(load_node(self._done[instance]).is_finished_ok for instance in self._instances[name])
        }

    @property
    def _failed(self) -> list[str]:
        """Return the tasks that finished without success, in the order in which they were declared."""
        finished, succeeded = self._finished, self._succeeded
        return [task.name for task in self.dag.tasks if task.name in finished and task.name not in succeeded]

    def _dispatch(self, name: str) -> None:
        """Submit the processes one task needs, which is one per item for a map and one for anything else."""
        task = self.dag.task(name)
        inputs = self._resolve_inputs(task)

        if isinstance(task, MapTask):
            self._dispatch_mapped(task, inputs)
            return

        self._instances[name] = [name]
        self._submit_instance(task, name, inputs)

    def _resolve_inputs(self, task: GraphTask) -> dict[str, t.Any]:
        """Return the inputs of a task, with whatever comes from another task filled in.

        A link never has a map as its source, since the declaration refuses that, so every source has run exactly
        one process and has one result to pass on.
        """
        inputs = dict(task.inputs)
        given = self.inputs.get(self._GRAPH_INPUTS, {})

        for name, targets in self.dag.inputs.items():
            if name not in given:
                continue

            for target, port in targets:
                if target == task.name:
                    inputs[port] = given[name]

        for link in self.dag.links:
            if link.target == task.name:
                inputs[link.target_port] = load_node(self._done[link.source]).outputs[link.source_port]

        return inputs

    def _dispatch_mapped(self, task: MapTask, inputs: dict[str, t.Any]) -> None:
        """Submit one process per item of the collection the task maps over."""
        items = _map_items(inputs.pop(task.item_port, None), task)
        self._instances[task.name] = [f'{task.name}_{key}' for key in items]

        for key, item in items.items():
            self._submit_instance(task, f'{task.name}_{key}', {**inputs, task.item_port: item})

        if not items:
            self.report(f'task `{task.name}` maps over an empty collection, so it runs nothing')

    def _submit_instance(self, task: GraphTask, instance: str, inputs: dict[str, t.Any]) -> None:
        """Submit one process of a task, under the name that its call link carries."""
        inputs = {**inputs, 'metadata': {**inputs.get('metadata', {}), 'call_link_label': instance}}
        node = self.submit(task.spec.process_class, **inputs)
        assert node.pk is not None
        self._dispatched[instance] = node.pk
        self.report(f'dispatched task `{instance}` as {node.pk}')

    @staticmethod
    def _item_key(name: str, instance: str) -> str:
        """Return the item a process ran for, which its instance name carries after the name of the task."""
        return instance[len(name) + 1 :]

    @override
    def on_wait(self, awaitables: t.Sequence[t.Awaitable]) -> None:
        """Ask to be woken when a dispatched task finishes.

        The callbacks are registered on entering the wait, so a task that finished while the graph was still
        dispatching is picked up rather than lost.
        """
        super().on_wait(awaitables)

        for name, pk in self._pending.items():
            self.runner.call_on_process_finish(pk, functools.partial(self.call_soon, self._on_task_finished, name, pk))

    def _on_task_finished(self, name: str, pk: int) -> None:
        """Record that a task finished and continue, which is what advances the graph."""
        self._done[name] = pk

        if self.state == ProcessState.WAITING:
            self.resume()

    def _finish(self) -> ExitCode | None:
        """Attach the declared outputs, or report the task that kept the graph from completing.

        A task that did not finish well leaves everything downstream of it unable to run, so the graph stops with
        the name of that task rather than dispatching a task whose inputs will never exist.
        """
        if self._failed:
            return self.exit_codes.ERROR_TASK_FAILED.format(task=self._failed[0])

        given = self.inputs.get(self._GRAPH_INPUTS, {})

        for output, source in self.dag.outputs.items():
            if source.task is None:
                # The graph passes one of its own inputs on, so the value is already there and nothing produced it.
                self.out(output, given[source.port])
                continue

            if not isinstance(self.dag.task(source.task), MapTask):
                self.out(output, load_node(self._done[source.task]).outputs[source.port])
                continue

            # A map produced a result per item, so the output is a namespace holding one entry per item.
            for instance in self._instances[source.task]:
                self.out(
                    f'{output}.{self._item_key(source.task, instance)}',
                    load_node(self._done[instance]).outputs[source.port],
                )

        return None
