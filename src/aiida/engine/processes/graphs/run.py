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
from collections.abc import Mapping
from dataclasses import dataclass, field

from aiida.engine.processes.graphs.inputs import at, place
from aiida.engine.processes.graphs.spec import GraphSpec, GraphTask, SubgraphTask, readable_version
from aiida.orm import Node, load_node

__all__ = ('GraphRun',)

STATE_VERSION = '0.1'





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


class GraphRunState(t.TypedDict, total=False):
    """The checkpointable scheduling progress of a graph run."""

    version: str
    instances: dict[str, list[str]]
    dispatched: dict[str, int]
    done: dict[str, int]
    skipped: list[str]


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

    @staticmethod
    def _is_finished_ok(pk: int) -> bool:
        return load_node(pk).is_finished_ok

    @property
    def succeeded(self) -> set[str]:
        return {
            name
            for name in self.finished
            if all(self._is_finished_ok(self.done[instance]) for instance in self.instances[name])
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

    def to_dict(self) -> GraphRunState:
        return {
            'version': STATE_VERSION,
            'instances': {name: list(runs) for name, runs in self.instances.items()},
            'dispatched': dict(self.dispatched),
            'done': dict(self.done),
            'skipped': sorted(self.skipped),
        }

    @classmethod
    def from_dict(cls, graph: GraphSpec, given: dict[str, t.Any], data: Mapping[str, t.Any]) -> GraphRun:
        """Rebuild the scheduling progress from a checkpoint."""
        readable_version(data.get('version', STATE_VERSION), STATE_VERSION, 'graph run')
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
        self.instances[name] = [name]
        step.begin(name, task, inputs, task.body if isinstance(task, SubgraphTask) else None)

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

    def _produced_by(self, name: str) -> Node:
        """Return the node produced by the latest instance of one task."""
        return load_node(self.done[self.instances[name][-1]])
