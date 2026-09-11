###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""How far a graph of tasks has got, and what it should do next."""

from __future__ import annotations

import typing as t
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field

from aiida.common.links import LinkType
from aiida.engine.processes.graphs.spec import (
    BranchTask,
    Dependency,
    GraphSpec,
    GraphTask,
    LoopTask,
    MapGraphTask,
    MappedTask,
    SubgraphTask,
)
from aiida.orm import Dict, List, Node, ProcessNode, load_node
from aiida.orm.nodes.data.base import BaseType

__all__ = ('GraphRun', 'Start', 'Step', 'TaskNodes', 'rerun_from', 'tasks')


def holds(condition: t.Any) -> bool:
    """Return whether a condition holds, on the value inside whatever node it arrives in.

    A stored value is not usefully truthy on its own, since a node is an object like any other and ``Int(0)`` is
    as truthy as ``Int(1)``, so it is the value it holds that decides.
    """
    return bool(condition.value if isinstance(condition, BaseType) else condition)


def at(container: t.Any, path: str) -> t.Any:
    """Return what sits at a path in something nested, which may name an output inside a namespace.

    :param path: name of a port, or names separated by dots for one inside a nested namespace.
    """
    value = container

    for name in path.split('.'):
        value = value[name]

    return value


def place(inputs: dict[str, t.Any], path: str, value: t.Any) -> None:
    """Put a value at a path in the inputs, making the namespaces the path names along the way.

    :raises ValueError: if a name on the way is already a value, which would put an input inside a value.
    """
    *namespaces, name = path.split('.')
    target = inputs

    for namespace in namespaces:
        target = target.setdefault(namespace, {})

        if not isinstance(target, dict):
            raise ValueError(f'`{path}` puts an input inside `{namespace}`, which is a value rather than a namespace.')

    target[name] = value


def returned(node: Node) -> dict[str, t.Any]:
    """Return what a graph produced, by the name each output was returned under."""
    return {entry.link_label: entry.node for entry in node.base.links.get_outgoing(link_type=LinkType.RETURN).all()}


class TaskNodes(Mapping[str, ProcessNode]):
    """The processes a graph ran, by the name the graph gave each of them.

    A task is addressed by its name, and one inside a graph that a task ran by the names on the way to it, joined
    by dots. A task that ran once per item is addressed by the name of each run, which carries the item after the
    name of the task.
    """

    def __init__(self, node: ProcessNode) -> None:
        self._node = node

    def __getitem__(self, path: str) -> ProcessNode:
        node = self._node
        reached: list[str] = []

        for name in path.split('.'):
            node = self._called(node, name, reached)
            reached.append(name)

        return node

    def __iter__(self) -> t.Iterator[str]:
        return iter(self._children(self._node))

    def __len__(self) -> int:
        return len(self._children(self._node))

    @classmethod
    def _called(cls, node: ProcessNode, name: str, reached: list[str]) -> ProcessNode:
        """Return the process one task ran, named among what the given node called.

        :raises KeyError: if nothing of that name ran, naming what did, since a task is left out of a run where
            the branch it sits in was not taken.
        :raises ValueError: if the name stands for more than one process, which a graph never does and a work
            chain submitting without a call link label does.
        """
        called = cls._children(node)
        where = f'`{".".join(reached)}`' if reached else f'<{node.pk}>'

        if name not in called:
            msg = f'{where} ran no task `{name}`. It ran {sorted(called)}.'
            raise KeyError(msg)

        if len(called[name]) > 1:
            # A node reached through a link is stored, so it has a pk.
            pks = sorted(t.cast(int, child.pk) for child in called[name])
            msg = (
                f'{where} called {len(pks)} processes `{name}`, {pks}, so the name does not say which. Give each '
                f'of them a `metadata.call_link_label` of its own, which a graph does for every task it runs.'
            )
            raise ValueError(msg)

        return called[name][0]

    @staticmethod
    def _children(node: ProcessNode) -> dict[str, list[ProcessNode]]:
        """Return the processes a node called, by the name each was called under.

        A name can stand for more than one process, since a work chain that submits without a call link label
        leaves every one of them under the default.
        """
        link_types = (LinkType.CALL_CALC, LinkType.CALL_WORK)
        called: dict[str, list[ProcessNode]] = defaultdict(list)

        for entry in node.base.links.get_outgoing(link_type=link_types).all():
            called[entry.link_label].append(t.cast(ProcessNode, entry.node))

        return called


def tasks(node: ProcessNode) -> TaskNodes:
    """Return the processes a graph ran, by the name the graph gave each of them.

    Every task of a graph is a process of its own, called under the name the graph knows it by, so this is what
    reaches one after the fact: its result, and the process to pause, play or kill.

    >>> from aiida.engine import tasks
    >>>
    >>> ran = tasks(node)
    >>> ran['relax'].outputs.energy
    >>> ran['refine.relax'].pk        # a task of a graph that a task ran
    >>> sorted(ran)                   # the tasks this graph ran, leaving out any that were skipped

    :param node: the node of the graph, or of any process, whose called processes to reach.
    """
    return TaskNodes(node)


def rerun_from(node: ProcessNode, *names: str) -> list[ProcessNode]:
    """Make the named tasks of a graph run again the next time the graph is run.

    Running a graph again takes every task from the cache, so nothing that has not changed is computed twice.
    This is what says which of them should be: the runs named here stop being usable as a cache source, so they
    run again, and so does anything downstream whose own inputs change as a result. Anything unaffected stays
    cached, which is what makes this a restart from a task rather than a rerun of everything after it.

    Naming nothing takes every task that did not finish well, at any depth, which is the common case: a graph
    that stopped somewhere is run again after the reason is fixed. That has to be said, because a task that
    failed is as valid a cache source as one that worked, so a graph run again would otherwise take the failure
    from the cache and stop in the same place.

    Caching has to be on for any of this to do anything, which is `verdi config set caching.default_enabled`.

    >>> from aiida.engine import rerun_from, submit
    >>>
    >>> rerun_from(node)                 # everything that did not finish well
    >>> rerun_from(node, 'relax')        # and this one as well, though it worked
    >>> submit(pipeline, **inputs)

    :param node: the node of the graph that ran.
    :param names: the tasks to run again, by the name the graph gave each of them, or none for those that did
        not finish well.
    :return: the nodes that will no longer be taken from the cache, which is every run the cache would have
        answered with rather than only the ones named.
    :raises KeyError: if a name is not a task of the graph.
    """
    ran = TaskNodes(node)
    chosen = [ran[name] for name in names] if names else _did_not_finish_well(node)
    forgotten: list[ProcessNode] = []

    for task in chosen:
        # Every run the cache would answer with, rather than this one alone: an earlier run of the same task on
        # the same inputs would be found in its place and the task would not run again after all.
        for same in [task, *t.cast(list[ProcessNode], task.base.caching.get_all_same_nodes())]:
            if same.pk not in {one.pk for one in forgotten}:
                same.base.caching.is_valid_cache = False
                forgotten.append(same)

    return forgotten


def _did_not_finish_well(node: ProcessNode) -> list[ProcessNode]:
    """Return every process under this one that did not finish well, however deep it sits."""
    return [called for called in node.called_descendants if not called.is_finished_ok]


def map_items(collection: t.Any, task: MappedTask) -> dict[str, t.Any]:
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
class Start:
    """One run to begin: the name its call link carries, what to run, and the inputs to run it on.

    What runs is either the task itself or a graph, and ``body`` is what says which. A branch and a loop pick
    theirs while the graph runs, so it cannot be read off the task alone.
    """

    instance: str
    task: GraphTask
    inputs: dict[str, t.Any]
    body: GraphSpec | None = None


@dataclass
class Step:
    """What a graph should do next, and what is worth saying about how it decided."""

    starts: list[Start] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def begin(self, instance: str, task: GraphTask, inputs: dict[str, t.Any], body: GraphSpec | None = None) -> None:
        """Record that one run should begin."""
        self.starts.append(Start(instance=instance, task=task, inputs=inputs, body=body))

    def note(self, text: str) -> None:
        """Record something worth telling whoever is watching the graph."""
        self.notes.append(text)


@dataclass
class GraphRun:
    """How far a graph has got, and what it should do next.

    This runs nothing and knows of no engine: given a declaration and what has finished, it says what to start and
    what to skip. That is what lets the same decisions be made by the process running the graph, or by something
    watching it from outside.
    """

    graph: GraphSpec
    given: dict[str, t.Any] = field(default_factory=dict)
    # What each task started, which is one run for most tasks and one per item for a fan-out. The runs are tracked
    # under an instance name, so a task that fans out needs no second kind of bookkeeping.
    instances: dict[str, list[str]] = field(default_factory=dict)
    dispatched: dict[str, int] = field(default_factory=dict)
    done: dict[str, int] = field(default_factory=dict)
    # Tasks that will never run, because a branch was not taken or because something they take an input from was
    # itself skipped. They settle like a task that finished, and produce nothing.
    skipped: set[str] = field(default_factory=set)

    @property
    def pending(self) -> dict[str, int]:
        """Return the runs that have been started but have not finished."""
        return {instance: pk for instance, pk in self.dispatched.items() if instance not in self.done}

    @property
    def finished(self) -> set[str]:
        """Return the tasks all of whose runs have finished, however they finished."""
        return {name for name, runs in self.instances.items() if all(instance in self.done for instance in runs)}

    @property
    def succeeded(self) -> set[str]:
        """Return the tasks that finished successfully, the only ones a next task can take inputs from.

        A task that fanned out counts as successful once every one of its runs did, so one failed item stops what
        comes after it just as a single failed task does.
        """
        return {
            name
            for name in self.finished
            if all(load_node(self.done[instance]).is_finished_ok for instance in self.instances[name])
        }

    @property
    def failed(self) -> list[str]:
        """Return the tasks that finished without success, in the order in which they were declared."""
        finished, succeeded = self.finished, self.succeeded
        return [task.name for task in self.graph.tasks if task.name in finished and task.name not in succeeded]

    @property
    def settled(self) -> set[str]:
        """Return the tasks the ones after them can be decided on: those that succeeded, and those that will not run."""
        return self.succeeded | self.skipped

    @property
    def decided(self) -> set[str]:
        """Return the tasks that have been started or skipped, which are the ones not to look at again."""
        return set(self.instances) | self.skipped

    def frontier(self) -> list[str]:
        """Return the tasks that could start now, deciding nothing.

        This is what something ordering several graphs against each other asks each of them, since it has to know
        what every one of them could do before saying which of them may. :meth:`step` is what decides, and it may
        begin more than this named: beginning a task can settle it without running anything, which makes the tasks
        after it ready in the same step.
        """
        going_round = [
            task.name
            for task in self.graph.tasks
            if isinstance(task, LoopTask) and task.name in self.instances and self._loop_may_run_again(task)
        ]

        return going_round + self.graph.ready(self.settled, self.decided)

    def step(self) -> Step:
        """Return the runs to begin now, recording what was decided on the way.

        Loops go first: one whose latest run finished has all of its runs done, and so would count as settled and
        let the tasks after it start, when it has another run to go. Beginning a task can also settle it without
        running anything, which makes the tasks after it ready in the same step, so the frontier is taken again
        until it is empty.
        """
        step = Step()

        for task in self.graph.tasks:
            if isinstance(task, LoopTask) and task.name in self.instances:
                self._continue_loop(task, step)

        while ready := self.graph.ready(self.settled, self.decided):
            for name in ready:
                self._begin(name, step)

        return step

    def started(self, instance: str, pk: int) -> None:
        """Record which process one run became."""
        self.dispatched[instance] = pk

    def completed(self, instance: str, pk: int) -> None:
        """Record that one run finished."""
        self.done[instance] = pk

    def outputs(self) -> dict[str, t.Any]:
        """Return what the graph produced, by the name each is returned under.

        A task that ran once per item produced a result per item, so it is returned under one name per item, which
        is why the names may be paths rather than plain names.
        """
        produced: dict[str, t.Any] = {}

        for output, source in self.graph.outputs.items():
            if source.task is None:
                # The graph passes one of its own inputs on, so the value is already there and nothing produced it.
                produced[output] = self.given[source.port]
                continue

            if source.task in self.skipped:
                continue

            if not isinstance(self.graph.task(source.task), MappedTask):
                produced[output] = at(self._produced_by(source.task).outputs, source.port)
                continue

            for instance in self.instances[source.task]:
                key = self._item_key(source.task, instance)
                produced[f'{output}.{key}'] = at(load_node(self.done[instance]).outputs, source.port)

        return produced

    def to_dict(self) -> dict[str, t.Any]:
        """Return how far the graph has got, as the checkpoint carries it."""
        return {
            'instances': {name: list(runs) for name, runs in self.instances.items()},
            'dispatched': dict(self.dispatched),
            'done': dict(self.done),
            'skipped': sorted(self.skipped),
        }

    @classmethod
    def from_dict(cls, graph: GraphSpec, given: dict[str, t.Any], data: dict[str, t.Any]) -> GraphRun:
        """Return how far a graph had got, from what was written out by :meth:`to_dict`."""
        return cls(
            graph=graph,
            given=given,
            instances={name: list(runs) for name, runs in data.get('instances', {}).items()},
            dispatched=dict(data.get('dispatched', {})),
            done=dict(data.get('done', {})),
            skipped=set(data.get('skipped', [])),
        )

    def _begin(self, name: str, step: Step) -> None:
        """Begin one task, unless something it takes an input from never ran, leaving it nothing to run on."""
        missing = sorted(self.graph.predecessors(name) & self.skipped)

        if missing:
            step.note(f'task `{name}` will not run, since `{missing[0]}` did not')
            self.skipped.add(name)
            return

        task = self.graph.task(name)
        inputs = self._inputs_for(task)

        if isinstance(task, BranchTask):
            self._begin_branch(task, inputs, step)
            return

        if isinstance(task, LoopTask):
            self._begin_loop(task, inputs, step)
            return

        if isinstance(task, MappedTask):
            self._begin_mapped(task, inputs, step)
            return

        self.instances[name] = [name]
        step.begin(name, task, inputs, self._body_of(task))

    def _begin_branch(self, task: BranchTask, inputs: dict[str, t.Any], step: Step) -> None:
        """Begin the branch the condition selects, and skip the task when it selects none."""
        condition = inputs.pop(task.condition_port, None)
        taken = task.body if holds(condition) else task.otherwise

        if taken is None:
            step.note(f'task `{task.name}` will not run, since its condition is false and it has no `otherwise`')
            self.skipped.add(task.name)
            return

        self.instances[task.name] = [task.name]
        step.begin(task.name, task, inputs, taken)

    def _begin_loop(self, task: LoopTask, inputs: dict[str, t.Any], step: Step) -> None:
        """Run the body a first time, and skip the loop when its condition does not hold to begin with.

        A loop given no value to start on goes round once and asks the body from then on, since a loop written
        without one is a loop meant to run.
        """
        if not holds(inputs.get(task.condition_port, True)):
            step.note(f'task `{task.name}` will not run, since `{task.condition_port}` is false to begin with')
            self.skipped.add(task.name)
            return

        self.instances[task.name] = []
        self._begin_iteration(task, inputs, step)

    def _continue_loop(self, task: LoopTask, step: Step) -> None:
        """Run the body once more, on what the run before it produced, while there is reason to."""
        if not self._loop_wants_another_run(task):
            return

        if len(self.instances[task.name]) >= task.max_iterations:
            step.note(
                f'task `{task.name}` ran {task.max_iterations} times, which is as many as it may, so it stops '
                f'with `{task.condition_port}` still true'
            )
            return

        produced = returned(load_node(self.done[self.instances[task.name][-1]]))
        self._begin_iteration(task, {**self._inputs_for(task), **produced}, step)

    def _loop_wants_another_run(self, task: LoopTask) -> bool:
        """Return whether the value a loop goes round on still holds, so that its body would run again."""
        runs = self.instances[task.name]

        if any(instance not in self.done for instance in runs):
            return False

        last = load_node(self.done[runs[-1]])

        return last.is_finished_ok and holds(returned(last).get(task.condition_port))

    def _loop_may_run_again(self, task: LoopTask) -> bool:
        """Return whether a loop has a run left to make, which it may though it has run before."""
        return self._loop_wants_another_run(task) and len(self.instances[task.name]) < task.max_iterations

    def _begin_iteration(self, task: LoopTask, state: dict[str, t.Any], step: Step) -> None:
        """Begin one run of the body, on the state the loop has reached."""
        instance = f'{task.name}_iteration_{len(self.instances[task.name])}'
        self.instances[task.name].append(instance)
        step.begin(instance, task, state, task.body)

    def _begin_mapped(self, task: MappedTask, inputs: dict[str, t.Any], step: Step) -> None:
        """Begin one run per item of the collection the task maps over, of whatever it runs."""
        items = map_items(inputs.pop(task.item_port, None), task)
        self.instances[task.name] = [f'{task.name}_{key}' for key in items]

        for key, item in items.items():
            step.begin(f'{task.name}_{key}', task, {**inputs, task.item_port: item}, self._body_of(task))

        if not items:
            step.note(f'task `{task.name}` maps over an empty collection, so it runs nothing')

    def _inputs_for(self, task: GraphTask) -> dict[str, t.Any]:
        """Return the inputs of a task, with whatever comes from another task filled in."""
        inputs = dict(task.inputs)

        for name, targets in self.graph.inputs.items():
            if name not in self.given:
                continue

            for target, port in targets:
                if target == task.name:
                    place(inputs, port, self.given[name])

        for edge in self.graph.dependencies:
            carried = edge.carried_between

            if edge.target != task.name or carried is None:
                continue

            source_port, target_port = carried

            if isinstance(self.graph.task(edge.source), MappedTask):
                place(inputs, target_port, self._gathered(edge, source_port))
            else:
                place(inputs, target_port, at(self._produced_by(edge.source).outputs, source_port))

        return inputs

    def _gathered(self, edge: Dependency, source_port: str) -> dict[str, t.Any]:
        """Return what a task that ran once per item produced, under the key of the item each run was for."""
        return {
            self._item_key(edge.source, instance): at(load_node(self.done[instance]).outputs, source_port)
            for instance in self.instances[edge.source]
        }

    def _produced_by(self, name: str) -> t.Any:
        """Return the node holding what a task produced, which for one that ran more than once is its last run."""
        return load_node(self.done[self.instances[name][-1]])

    @staticmethod
    def _body_of(task: GraphTask) -> GraphSpec | None:
        """Return the graph a task runs, or ``None`` where it runs a process instead."""
        return task.body if isinstance(task, (SubgraphTask, MapGraphTask)) else None

    @staticmethod
    def _item_key(name: str, instance: str) -> str:
        """Return the item a run was for, which its instance name carries after the name of the task."""
        return instance[len(name) + 1 :]
