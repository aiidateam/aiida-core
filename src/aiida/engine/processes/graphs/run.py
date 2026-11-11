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
from collections.abc import Mapping, Set
from dataclasses import dataclass, field

from aiida.common.exceptions import GraphMaxIterationsError, GraphRuntimeError
from aiida.common.links import LinkType
from aiida.engine.processes.graphs.inputs import _at, _drops_none_value, _place
from aiida.engine.processes.graphs.ir import (
    BranchControl,
    GraphIR,
    GraphTask,
    LoopControl,
    ProcessTask,
    SubgraphTask,
    _input_ports_at,
    _require_version,
)
from aiida.engine.processes.graphs.shapes import LeafShape, NamespaceShape
from aiida.orm import Node, load_node
from aiida.orm.nodes.data.bool import Bool

__all__ = ('GraphRun',)

_STATE_VERSION = '0.1'


def _holds(condition: t.Any) -> bool:
    """Return whether a condition holds, accepting only `bool` and `Bool` values.
    Anything else fails loudly: truthiness coercion would silently treat `Int(0)` as false.
    """
    if isinstance(condition, bool):
        return condition
    if isinstance(condition, Bool):
        return bool(condition.value)
    msg = f'graph condition must be a `bool` or `Bool`, not `{type(condition)}`.'
    raise GraphRuntimeError(msg)


def _missing_declared_outputs(declared: NamespaceShape, node: Node) -> list[str]:
    """Return the declared dynamic outputs a finished task did not produce.

    The process spec leaves these outputs dynamic, so the process itself never enforces them.
    """
    produced = set(node.base.links.get_outgoing().all_link_labels())
    return [name for name, _ in declared.fields if name not in produced]


def _mistyped_declared_outputs(declared: NamespaceShape, node: Node) -> list[str]:
    """Return a message per declared output that a finished task produced with another node type.

    Declared types narrow the process spec, which keeps its broad ports and so accepts the value.
    """
    produced: dict[str, Node] = {
        entry.link_label: entry.node
        for entry in node.base.links.get_outgoing(link_type=(LinkType.CREATE, LinkType.RETURN)).all()
    }
    messages: list[str] = []
    for name, shape in declared.fields:
        value: Node | None = produced.get(name)
        if value is None or not isinstance(shape, LeafShape) or not shape.types or isinstance(value, shape.types):
            continue
        expected: str = ', '.join(kind.__name__ for kind in shape.types)
        messages.append(f'returned `{type(value).__name__}` for port `{name}`, expected `{expected}`')
    return messages


def _returned(node: Node) -> dict[str, t.Any]:
    """Read the returned outputs of one loop iteration."""
    return {entry.link_label: entry.node for entry in node.base.links.get_outgoing(link_type=LinkType.RETURN).all()}


@dataclass(frozen=True)
class _Start:
    """A run to dispatch under an explicit provenance call-link name."""

    instance: str
    task: GraphTask
    inputs: dict[str, t.Any]
    body: GraphIR | None = None


def _drops_none(task: GraphTask, path: str) -> bool:
    """Return whether a `None` value leaves an input unwired instead of failing validation."""
    ports = _input_ports_at(task, path)
    return bool(ports) and all(_drops_none_value(port) for port in ports)


@dataclass
class _Step:
    """The dispatches decided by one scheduling step."""

    starts: list[_Start] = field(default_factory=list)

    def begin(self, instance: str, task: GraphTask, inputs: dict[str, t.Any], body: GraphIR | None = None) -> None:
        """Record the dispatch of one task instance within this step."""
        self.starts.append(_Start(instance=instance, task=task, inputs=inputs, body=body))


class _GraphRunState(t.TypedDict, total=False):
    """The checkpointable scheduling progress of a graph run."""

    version: str
    instances: dict[str, list[str]]
    dispatched: dict[str, int]
    done: dict[str, int]
    passed: dict[str, dict[str, t.Any]]


@dataclass
class GraphRun:
    """How far a graph has progressed; dispatch itself belongs to GraphProcess."""

    graph: GraphIR
    given: dict[str, t.Any] = field(default_factory=dict)
    instances: dict[str, list[str]] = field(default_factory=dict)
    dispatched: dict[str, int] = field(default_factory=dict)
    done: dict[str, int] = field(default_factory=dict)
    passed: dict[str, dict[str, t.Any]] = field(default_factory=dict)
    _ok: dict[int, bool] = field(default_factory=dict, repr=False, compare=False)

    @property
    def pending(self) -> dict[str, int]:
        """Return the dispatched instances that have not completed yet."""
        return {instance: pk for instance, pk in self.dispatched.items() if instance not in self.done}

    @property
    def finished(self) -> set[str]:
        """Return the tasks whose instances all completed or passed state through."""
        return {
            name
            for name, runs in self.instances.items()
            if name in self.passed or all(instance in self.done for instance in runs)
        }

    def _is_finished_ok(self, pk: int) -> bool:
        """Return whether a finished node succeeded, caching the answer per node."""
        if pk not in self._ok:
            self._ok[pk] = load_node(pk).is_finished_ok
        return self._ok[pk]

    @property
    def succeeded(self) -> set[str]:
        """Return the finished tasks whose outputs all finished successfully."""
        return {
            name
            for name in self.finished
            if name in self.passed
            or (
                all(self._is_finished_ok(self.done[instance]) for instance in self.instances[name])
                and not self.missing_outputs(name)
                and not self.mistyped_outputs(name)
            )
        }

    def missing_outputs(self, name: str) -> list[str]:
        """Return the declared outputs the latest instance of a finished task did not produce."""
        task = self.graph.task(name)
        if not isinstance(task, ProcessTask) or not task.spec.declared_outputs.fields:
            return []
        return _missing_declared_outputs(task.spec.declared_outputs, self._produced_by(name))

    def mistyped_outputs(self, name: str) -> list[str]:
        """Return a message per declared output the latest instance of a finished task produced with another type."""
        task = self.graph.task(name)
        if not isinstance(task, ProcessTask) or not task.spec.declared_outputs.fields:
            return []
        return _mistyped_declared_outputs(task.spec.declared_outputs, self._produced_by(name))

    @property
    def failed(self) -> list[str]:
        """Return the finished tasks with at least one unsuccessful output, in graph order."""
        finished, succeeded = self.finished, self.succeeded
        return [name for name in self.graph.task_names if name in finished and name not in succeeded]

    def step(self) -> _Step:
        """Advance scheduling: continue loops, then dispatch every ready task."""
        step = _Step()
        for task in self.graph.tasks:
            if isinstance(task, LoopControl) and task.name in self.instances:
                self._continue_loop(task, step)
        succeeded = self.succeeded
        while ready := self._ready(succeeded | self.passed.keys()):
            for name in ready:
                self._begin(name, step)
        return step

    def _ready(self, done: Set[str]) -> list[str]:
        """Return the undispatched tasks whose predecessors are all done."""
        return [
            name
            for name in self.graph.task_names
            if name not in self.instances and self.graph.predecessors(name) <= done
        ]

    def started(self, instance: str, pk: int) -> None:
        """Record the node dispatched for one task instance."""
        self.dispatched[instance] = pk

    def completed(self, instance: str, pk: int) -> None:
        """Record the node produced by one task instance."""
        self.done[instance] = pk

    def outputs(self) -> dict[str, t.Any]:
        """Collect the graph outputs from passthrough inputs and task results."""
        produced = {}
        for output, source in self.graph.outputs.items():
            if source.task is None:
                produced[output] = _at(self.given, source.port)
            elif source.task in self.passed:
                produced[output] = _at(self.passed[source.task], source.port)
            else:
                produced[output] = _at(self._produced_by(source.task).outputs, source.port)
        return produced

    def to_dict(self) -> _GraphRunState:
        """Return the checkpointable scheduling progress, without the graph or inputs."""
        return {
            'version': _STATE_VERSION,
            'instances': {name: list(runs) for name, runs in self.instances.items()},
            'dispatched': dict(self.dispatched),
            'done': dict(self.done),
            'passed': {name: dict(outputs) for name, outputs in self.passed.items()},
        }

    @classmethod
    def from_dict(cls, graph: GraphIR, given: dict[str, t.Any], data: Mapping[str, t.Any]) -> GraphRun:
        """Rebuild the scheduling progress from a checkpoint."""
        _require_version(data.get('version', _STATE_VERSION), _STATE_VERSION, 'graph run')
        return cls(
            graph=graph,
            given=given,
            instances={name: list(runs) for name, runs in data.get('instances', {}).items()},
            dispatched=dict(data.get('dispatched', {})),
            done=dict(data.get('done', {})),
            passed={name: dict(outputs) for name, outputs in data.get('passed', {}).items()},
        )

    def _begin(self, name: str, step: _Step) -> None:
        """Dispatch one ready task."""
        task = self.graph.task(name)
        inputs = self._inputs_for(task)
        if isinstance(task, BranchControl):
            self._begin_branch(task, inputs, step)
        elif isinstance(task, LoopControl):
            self._begin_loop(task, inputs, step)
        else:
            self.instances[name] = [name]
            step.begin(name, task, inputs, task.body if isinstance(task, SubgraphTask) else None)

    def _begin_branch(self, task: BranchControl, inputs: dict[str, t.Any], step: _Step) -> None:
        """Dispatch the taken side of a branch."""
        taken = task.body if _holds(inputs.pop(task.condition_port)) else task.otherwise
        self.instances[task.name] = [task.name]
        # Each side may consume a different subset of the enclosing inputs.
        step.begin(task.name, task, {key: value for key, value in inputs.items() if key in taken.inputs}, taken)

    def _begin_loop(self, task: LoopControl, inputs: dict[str, t.Any], step: _Step) -> None:
        """Start iterating a loop, or pass through never-entered initial state."""
        if task.condition_port not in inputs:
            msg = f'loop `{task.name}` is missing its condition port `{task.condition_port}`.'
            raise GraphRuntimeError(msg)
        if not _holds(inputs[task.condition_port]):
            self._pass_initial_state(task, inputs)
            return
        self.instances[task.name] = []
        self._begin_iteration(task, inputs, step)

    def _pass_initial_state(self, task: LoopControl, inputs: dict[str, t.Any]) -> None:
        """Complete a never-entered loop with its initial state, like Python would."""
        self.instances[task.name] = [task.name]
        self.passed[task.name] = {name: inputs[name] for name in task.body.outputs if name in inputs}

    def _continue_loop(self, task: LoopControl, step: _Step) -> None:
        """Dispatch the next iteration once the previous one finished successfully."""
        runs = self.instances[task.name]
        if not runs or any(instance not in self.done for instance in runs):
            return
        if not self._is_finished_ok(self.done[runs[-1]]):
            return
        last = load_node(self.done[runs[-1]])
        outputs = _returned(last)
        if task.condition_port not in outputs:
            msg = f'loop `{task.name}` is missing its condition port `{task.condition_port}`.'
            raise GraphRuntimeError(msg)
        if not _holds(outputs[task.condition_port]):
            return
        if len(runs) >= task.max_iterations:
            msg = f'loop `{task.name}` exceeded {task.max_iterations} iterations; check that its condition terminates.'
            raise GraphMaxIterationsError(msg)
        self._begin_iteration(task, {**self._inputs_for(task), **outputs}, step)

    def _begin_iteration(self, task: LoopControl, inputs: dict[str, t.Any], step: _Step) -> None:
        """Dispatch one numbered loop iteration over the loop body."""
        instance = f'{task.name}_iteration_{len(self.instances[task.name])}'
        self.instances[task.name].append(instance)
        step.begin(
            instance, task, {name: value for name, value in inputs.items() if name in task.body.inputs}, task.body
        )

    def _inputs_for(self, task: GraphTask) -> dict[str, t.Any]:
        """Wire graph inputs and dependency outputs into one task's declared inputs."""

        # Namespace dictionaries are mutable during wiring; never mutate the saved declaration.
        def copy(value: t.Any) -> t.Any:
            return {name: copy(item) for name, item in value.items()} if isinstance(value, dict) else value

        inputs = copy(task.inputs)
        for name, targets in self.graph.inputs.items():
            try:
                value = _at(self.given, name)
            except KeyError:
                continue
            for target, port in targets:
                if target == task.name:
                    if value is None and _drops_none(task, port):
                        # An explicit `None` on an optional input leaves the input unwired.
                        continue
                    _place(inputs, port, value)
        for edge in self.graph.dependencies:
            if edge.target == task.name and edge.carried_between is not None:
                source, target = edge.carried_between
                if edge.source in self.passed:
                    value = _at(self.passed[edge.source], source)
                else:
                    value = _at(self._produced_by(edge.source).outputs, source)
                if value is None and _drops_none(task, target):
                    # An absent arm on an optional input means the input is unwired.
                    continue
                _place(inputs, target, value)
        return inputs

    def _produced_by(self, name: str) -> Node:
        """Return the node produced by the latest instance of one task."""
        return load_node(self.done[self.instances[name][-1]])
