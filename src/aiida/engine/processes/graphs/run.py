###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Checkpointable scheduling decisions for static task graphs."""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from aiida.common.links import LinkType
from aiida.engine.processes.graphs.inputs import at
from aiida.engine.processes.graphs.spec import BranchControl, GraphSpec, GraphTask, LoopControl, SubgraphTask
from aiida.orm import Node, load_node
from aiida.orm.nodes.data.base import BaseType

__all__ = ('GraphRun',)


def holds(condition: t.Any) -> bool:
    """Evaluate the value of a condition node rather than the node's identity."""
    return bool(condition.value if isinstance(condition, BaseType) else condition)


def place(inputs: dict[str, t.Any], path: str, value: t.Any) -> None:
    """Place a leaf or namespace reference without flattening dictionary-valued leaves."""
    *namespaces, name = path.split('.')
    target = inputs
    for namespace in namespaces:
        target = target.setdefault(namespace, {})
        if not isinstance(target, dict):
            msg = f'`{path}` puts an input inside a value rather than a namespace.'
            raise ValueError(msg)
    target[name] = value


def returned(node: Node) -> dict[str, t.Any]:
    """Read the leaf outputs of one graph iteration."""
    return {entry.link_label: entry.node for entry in node.base.links.get_outgoing(link_type=LinkType.RETURN).all()}


@dataclass(frozen=True)
class Start:
    """A run to dispatch under an explicit provenance call-link name."""

    instance: str
    task: GraphTask
    inputs: dict[str, t.Any]
    body: GraphSpec | None = None


@dataclass
class Step:
    starts: list[Start] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def begin(self, instance: str, task: GraphTask, inputs: dict[str, t.Any], body: GraphSpec | None = None) -> None:
        self.starts.append(Start(instance=instance, task=task, inputs=inputs, body=body))

    def note(self, text: str) -> None:
        self.notes.append(text)


@dataclass
class GraphRun:
    """How far a graph has progressed; dispatch itself belongs to GraphProcess."""

    graph: GraphSpec
    given: dict[str, t.Any] = field(default_factory=dict)
    instances: dict[str, list[str]] = field(default_factory=dict)
    dispatched: dict[str, int] = field(default_factory=dict)
    done: dict[str, int] = field(default_factory=dict)
    skipped: set[str] = field(default_factory=set)

    @property
    def pending(self) -> dict[str, int]:
        return {instance: pk for instance, pk in self.dispatched.items() if instance not in self.done}

    @property
    def finished(self) -> set[str]:
        return {name for name, runs in self.instances.items() if all(instance in self.done for instance in runs)}

    @property
    def succeeded(self) -> set[str]:
        return {
            name
            for name in self.finished
            if all(load_node(self.done[instance]).is_finished_ok for instance in self.instances[name])
        }

    @property
    def failed(self) -> list[str]:
        return [name for name in self.graph.task_names if name in self.finished and name not in self.succeeded]

    @property
    def settled(self) -> set[str]:
        return self.succeeded | self.skipped

    @property
    def decided(self) -> set[str]:
        return set(self.instances) | self.skipped

    def step(self) -> Step:
        step = Step()
        for task in self.graph.tasks:
            if isinstance(task, LoopControl) and task.name in self.instances:
                self._continue_loop(task, step)
        while ready := self.graph.ready(self.settled, self.decided):
            for name in ready:
                self._begin(name, step)
        return step

    def started(self, instance: str, pk: int) -> None:
        self.dispatched[instance] = pk

    def completed(self, instance: str, pk: int) -> None:
        self.done[instance] = pk

    def outputs(self) -> dict[str, t.Any]:
        produced = {}
        for output, source in self.graph.outputs.items():
            if source.task is None:
                produced[output] = at(self.given, source.port)
            elif source.task not in self.skipped:
                produced[output] = at(self._produced_by(source.task).outputs, source.port)
        return produced

    def to_dict(self) -> dict[str, t.Any]:
        return {
            'instances': {name: list(runs) for name, runs in self.instances.items()},
            'dispatched': dict(self.dispatched),
            'done': dict(self.done),
            'skipped': sorted(self.skipped),
        }

    @classmethod
    def from_dict(cls, graph: GraphSpec, given: dict[str, t.Any], data: dict[str, t.Any]) -> GraphRun:
        return cls(
            graph=graph,
            given=given,
            instances={name: list(runs) for name, runs in data.get('instances', {}).items()},
            dispatched=dict(data.get('dispatched', {})),
            done=dict(data.get('done', {})),
            skipped=set(data.get('skipped', ())),
        )

    def _begin(self, name: str, step: Step) -> None:
        missing = sorted(self.graph.predecessors(name) & self.skipped)
        if missing:
            step.note(f'task `{name}` will not run, since `{missing[0]}` did not')
            self.skipped.add(name)
            return
        task = self.graph.task(name)
        inputs = self._inputs_for(task)
        if isinstance(task, BranchControl):
            taken = task.body if holds(inputs.pop(task.condition_port, None)) else task.otherwise
            if taken is None:
                self.skipped.add(name)
                return
            self.instances[name] = [name]
            # Each side may consume a different subset of the enclosing inputs.
            step.begin(name, task, {key: value for key, value in inputs.items() if key in taken.inputs}, taken)
        elif isinstance(task, LoopControl):
            if not holds(inputs.get(task.condition_port, True)):
                self.skipped.add(name)
                return
            self.instances[name] = []
            self._begin_iteration(task, inputs, step)
        else:
            self.instances[name] = [name]
            step.begin(name, task, inputs, task.body if isinstance(task, SubgraphTask) else None)

    def _continue_loop(self, task: LoopControl, step: Step) -> None:
        runs = self.instances[task.name]
        if not runs or any(instance not in self.done for instance in runs):
            return
        last = load_node(self.done[runs[-1]])
        if not last.is_finished_ok or not holds(returned(last).get(task.condition_port)):
            return
        if len(runs) >= task.max_iterations:
            msg = f'loop `{task.name}` exceeded {task.max_iterations} iterations with its condition still true.'
            raise RuntimeError(msg)
        self._begin_iteration(task, {**self._inputs_for(task), **returned(last)}, step)

    def _begin_iteration(self, task: LoopControl, inputs: dict[str, t.Any], step: Step) -> None:
        instance = f'{task.name}_iteration_{len(self.instances[task.name])}'
        self.instances[task.name].append(instance)
        step.begin(
            instance, task, {name: value for name, value in inputs.items() if name in task.body.inputs}, task.body
        )

    def _inputs_for(self, task: GraphTask) -> dict[str, t.Any]:
        # Namespace dictionaries are mutable during wiring; never mutate the saved declaration.
        def copy(value: t.Any) -> t.Any:
            return {name: copy(item) for name, item in value.items()} if isinstance(value, dict) else value

        inputs = copy(task.inputs)
        for name, targets in self.graph.inputs.items():
            try:
                value = at(self.given, name)
            except KeyError:
                continue
            for target, port in targets:
                if target == task.name:
                    place(inputs, port, value)
        for edge in self.graph.dependencies:
            if edge.target == task.name and edge.carried_between is not None:
                source, target = edge.carried_between
                place(inputs, target, at(self._produced_by(edge.source).outputs, source))
        return inputs

    def _produced_by(self, name: str) -> t.Any:
        return load_node(self.done[self.instances[name][-1]])
