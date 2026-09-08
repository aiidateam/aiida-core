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
from aiida.orm import Dict, WorkChainNode, load_node

__all__ = ('Dependency', 'GraphProcess', 'GraphSpec', 'GraphTask')

SPEC_VERSION: str = '1.0'
"""Version of the graph declaration format, stored with every serialized spec."""


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


@dataclass(frozen=True)
class GraphTask:
    """A task placed in a graph, under a name, with the inputs that are given directly."""

    name: str
    spec: TaskSpec
    inputs: dict[str, t.Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, t.Any]:
        return {'name': self.name, 'spec': self.spec.to_dict(), 'inputs': self.inputs}

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> GraphTask:
        return cls(name=data['name'], spec=TaskSpec.from_dict(data['spec']), inputs=data.get('inputs', {}))


@dataclass(frozen=True)
class GraphSpec:
    """Declarative description of a graph of tasks.

    The graph is a template: it records which tasks to run, which output of one feeds which input of another, and
    which of those outputs the graph itself returns. It runs nothing, and holds no results.
    """

    tasks: tuple[GraphTask, ...]
    links: tuple[Dependency, ...] = ()
    outputs: dict[str, tuple[str, str]] = field(default_factory=dict)
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

        for output, (name, port) in self.outputs.items():
            if name not in names:
                raise ValueError(f'output `{output}` refers to unknown task `{name}`.')

            outputs = self.task(name).spec.outputs

            if port not in outputs and not outputs.dynamic:
                raise ValueError(f'output `{output}` refers to `{port}`, which is not an output of `{name}`.')

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
            'outputs': {name: list(target) for name, target in self.outputs.items()},
            'version': self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> GraphSpec:
        return cls(
            tasks=tuple(GraphTask.from_dict(task) for task in data['tasks']),
            links=tuple(Dependency.from_dict(link) for link in data.get('links', [])),
            outputs={name: (target[0], target[1]) for name, target in data.get('outputs', {}).items()},
            version=data.get('version', SPEC_VERSION),
        )


class GraphProcess(Process):
    """Run a graph of tasks, dispatching each as a child process.

    Every task that is ready is submitted, so it is a process in its own right: it gets its own node, its own entry
    in the provenance graph under the name the graph gave it, and it is scheduled like any other process. The graph
    keeps only the bookkeeping of what it dispatched and what has finished, which travels with its checkpoint.
    """

    _node_class = WorkChainNode

    _DAG = 'dag'

    @classmethod
    def define(cls, spec: ProcessSpec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input(cls._DAG, valid_type=Dict, help='The declaration of the graph to run.')
        spec.outputs.dynamic = True
        spec.exit_code(400, 'ERROR_TASK_FAILED', message='The task `{task}` did not finish successfully.')

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self._dag: GraphSpec | None = None
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
        out_state['dispatched'] = dict(self._dispatched)
        out_state['done'] = dict(self._done)

    @override
    def load_instance_state(self, saved_state: MutableMapping[str, t.Any], load_context: t.Any) -> None:
        super().load_instance_state(saved_state, load_context)
        self._dag = None
        self._dispatched = dict(saved_state.get('dispatched', {}))
        self._done = dict(saved_state.get('done', {}))

    @override
    async def run(self) -> t.Any:
        return self._do_step()

    def _do_step(self) -> t.Any:
        """Dispatch the tasks that are ready, and wait until something finishes."""
        for name in self.dag.ready(self._succeeded, self._dispatched):
            self._dispatch(name)

        if self._pending:
            return Wait(self._do_step, 'waiting for dispatched tasks')

        return self._finish()

    @property
    def _pending(self) -> dict[str, int]:
        """Return the tasks that have been dispatched but have not finished."""
        return {name: pk for name, pk in self._dispatched.items() if name not in self._done}

    @property
    def _succeeded(self) -> set[str]:
        """Return the tasks that finished successfully, which are the only ones a next task can take inputs from."""
        return {name for name, pk in self._done.items() if load_node(pk).is_finished_ok}

    @property
    def _failed(self) -> list[str]:
        """Return the tasks that finished without success, in the order in which they were declared."""
        return [task.name for task in self.dag.tasks if task.name in self._done and task.name not in self._succeeded]

    def _dispatch(self, name: str) -> None:
        """Submit one task as a child process."""
        task = self.dag.task(name)
        inputs = dict(task.inputs)

        for link in self.dag.links:
            if link.target == name:
                inputs[link.target_port] = load_node(self._done[link.source]).outputs[link.source_port]

        inputs['metadata'] = {**inputs.get('metadata', {}), 'call_link_label': name}
        node = self.submit(task.spec.process_class, **inputs)
        assert node.pk is not None
        self._dispatched[name] = node.pk
        self.report(f'dispatched task `{name}` as {node.pk}')

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

        for output, (name, port) in self.dag.outputs.items():
            self.out(output, load_node(self._done[name]).outputs[port])

        return None
