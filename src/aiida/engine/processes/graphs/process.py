###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Execution of a graph of tasks on the process state machine."""

from __future__ import annotations

import collections.abc
import functools
import typing as t
from collections.abc import MutableMapping

from aiida.common.lang import override
from aiida.common.processes import ProcessState
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.functions import FunctionProcess
from aiida.engine.processes.graphs.spec import (
    BranchTask,
    GraphSpec,
    GraphTask,
    MapTask,
    ProcessTask,
    SubgraphTask,
)
from aiida.engine.processes.process import Process
from aiida.engine.processes.process_spec import ProcessSpec
from aiida.engine.processes.states import Wait
from aiida.orm import Data, Dict, List, WorkChainNode, load_node
from aiida.orm.nodes.data.base import BaseType, to_aiida_type

__all__ = ('GraphProcess', 'TaskProcess')


class TaskProcess(FunctionProcess):
    """A :class:`FunctionProcess` whose wrapped function takes and returns plain Python values.

    Values that are not already a ``Data`` node are serialized with ``to_aiida_type``, mirroring the serialization
    that the input ports of a function process already perform. When the task declares its output ports, a returned
    tuple is mapped onto them in order.
    """

    @override
    def _out_result(self, result: t.Any) -> None:
        declared = list(self.spec().outputs.keys())

        if not self.spec().outputs.dynamic and not isinstance(result, collections.abc.Mapping):
            values = result if isinstance(result, tuple) else (result,)

            if len(values) != len(declared):
                raise ValueError(
                    f'`{self.process_class.__name__}` declares {len(declared)} outputs {declared} but the function '
                    f'returned {len(values)} value(s).'
                )

            result = dict(zip(declared, values, strict=True))

        if isinstance(result, collections.abc.Mapping):
            result = {key: value if isinstance(value, Data) else to_aiida_type(value) for key, value in result.items()}
        elif not isinstance(result, Data):
            result = to_aiida_type(result)

        super()._out_result(result)


def _holds(condition: t.Any) -> bool:
    """Return whether a condition holds, on the value inside whatever node it arrives in.

    A stored value is not usefully truthy on its own, since a node is an object like any other and ``Int(0)`` is
    as truthy as ``Int(1)``, so it is the value it holds that decides.
    """
    return bool(condition.value if isinstance(condition, BaseType) else condition)


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


class GraphProcess(Process):
    """Run a graph of tasks, dispatching each as a child process.

    Every task that is ready is submitted, so it is a process in its own right: it gets its own node, its own entry
    in the provenance graph under the name the graph gave it, and it is scheduled like any other process. The graph
    keeps only the bookkeeping of what it dispatched and what has finished, which travels with its checkpoint.
    """

    _node_class = WorkChainNode

    _GRAPH = 'graph'
    _GRAPH_INPUTS = 'graph_inputs'

    @classmethod
    def define(cls, spec: ProcessSpec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input(cls._GRAPH, valid_type=Dict, help='The declaration of the graph to run.')
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
        self._graph: GraphSpec | None = None
        # What each task dispatched, which is one process for most tasks and one per item for a map. The processes
        # are tracked under an instance name, so a task that fans out needs no second kind of bookkeeping.
        self._instances: dict[str, list[str]] = {}
        self._dispatched: dict[str, int] = {}
        self._done: dict[str, int] = {}
        # Tasks that will never run, because a branch was not taken or because something they take an input from
        # was itself skipped. They settle like a task that finished, but produce nothing.
        self._skipped: set[str] = set()

    @property
    def graph(self) -> GraphSpec:
        """Return the declaration of the graph being run."""
        if self._graph is None:
            self._graph = GraphSpec.from_dict(self.inputs[self._GRAPH].get_dict())
        return self._graph

    @classmethod
    def launch_inputs(cls, body: GraphSpec, inputs: dict[str, t.Any]) -> dict[str, t.Any]:
        """Return the inputs with which to launch a graph: the declaration, and the values to run it on.

        The two travel side by side, so one declaration serves every run. The values are serialized here because
        they arrive in a dynamic namespace, which declares no ports of its own to do it.

        :param body: the graph to run.
        :param inputs: the values for the inputs the graph declares.
        """
        return {
            cls._GRAPH: Dict(dict=body.to_dict()),
            cls._GRAPH_INPUTS: {
                name: value if isinstance(value, Data) else to_aiida_type(value) for name, value in inputs.items()
            },
        }

    @override
    def save_instance_state(self, out_state: MutableMapping[str, t.Any], save_context: t.Any) -> None:
        super().save_instance_state(out_state, save_context)
        out_state['instances'] = {name: list(instances) for name, instances in self._instances.items()}
        out_state['dispatched'] = dict(self._dispatched)
        out_state['done'] = dict(self._done)
        out_state['skipped'] = sorted(self._skipped)

    @override
    def load_instance_state(self, saved_state: MutableMapping[str, t.Any], load_context: t.Any) -> None:
        super().load_instance_state(saved_state, load_context)
        self._graph = None
        self._instances = {name: list(instances) for name, instances in saved_state.get('instances', {}).items()}
        self._dispatched = dict(saved_state.get('dispatched', {}))
        self._done = dict(saved_state.get('done', {}))
        self._skipped = set(saved_state.get('skipped', []))

    @override
    async def run(self) -> t.Any:
        return self._do_step()

    def _do_step(self) -> t.Any:
        """Start the tasks that are ready, and wait until something finishes.

        Starting a task can settle it without running anything, which makes the tasks after it ready in the
        same step, so the frontier is taken again until it is empty.
        """
        while ready := self.graph.ready(self._settled, self._decided):
            for name in ready:
                self._start(name)

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
        return [task.name for task in self.graph.tasks if task.name in finished and task.name not in succeeded]

    @property
    def _settled(self) -> set[str]:
        """Return the tasks the ones after them can be decided on: those that succeeded, and those that will not run."""
        return self._succeeded | self._skipped

    @property
    def _decided(self) -> set[str]:
        """Return the tasks that have been started or skipped, which are the ones not to look at again."""
        return set(self._instances) | self._skipped

    def _start(self, name: str) -> None:
        """Start one task, unless something it takes an input from never ran, which leaves it nothing to run on."""
        missing = sorted(self.graph.predecessors(name) & self._skipped)

        if missing:
            self.report(f'task `{name}` will not run, since `{missing[0]}` did not')
            self._skipped.add(name)
            return

        task = self.graph.task(name)
        inputs = self._resolve_inputs(task)

        if isinstance(task, BranchTask):
            self._dispatch_branch(task, inputs)
            return

        if isinstance(task, MapTask):
            self._dispatch_mapped(task, inputs)
            return

        self._instances[name] = [name]
        self._submit_instance(task, name, inputs)

    def _dispatch_branch(self, task: BranchTask, inputs: dict[str, t.Any]) -> None:
        """Submit the branch the condition selects, and skip the task when it selects none."""
        condition = inputs.pop(task.condition_port, None)
        taken = task.body if _holds(condition) else task.otherwise

        if taken is None:
            self.report(f'task `{task.name}` will not run, since its condition is false and it has no `otherwise`')
            self._skipped.add(task.name)
            return

        self._instances[task.name] = [task.name]
        self._submit(GraphProcess, GraphProcess.launch_inputs(taken, inputs), task.name)

    def _resolve_inputs(self, task: GraphTask) -> dict[str, t.Any]:
        """Return the inputs of a task, with whatever comes from another task filled in.

        A link never has a map as its source, since the declaration refuses that, so every source has run exactly
        one process and has one result to pass on.
        """
        inputs = dict(task.inputs)
        given = self.inputs.get(self._GRAPH_INPUTS, {})

        for name, targets in self.graph.inputs.items():
            if name not in given:
                continue

            for target, port in targets:
                if target == task.name:
                    inputs[port] = given[name]

        for edge in self.graph.dependencies:
            if edge.target == task.name:
                inputs[edge.target_port] = load_node(self._done[edge.source]).outputs[edge.source_port]

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
        """Submit one process of a task, with whatever runs it."""
        process_class, launch_inputs = self._launch(task, inputs)
        self._submit(process_class, launch_inputs, instance)

    def _submit(self, process_class: type[Process], inputs: dict[str, t.Any], instance: str) -> None:
        """Submit one process, under the name that its call link carries."""
        metadata = {**inputs.get('metadata', {}), 'call_link_label': instance}
        node = self.submit(process_class, **{**inputs, 'metadata': metadata})
        assert node.pk is not None
        self._dispatched[instance] = node.pk
        self.report(f'dispatched task `{instance}` as {node.pk}')

    @staticmethod
    def _launch(task: GraphTask, inputs: dict[str, t.Any]) -> tuple[type[Process], dict[str, t.Any]]:
        """Return the process that runs one instance of a task, and the inputs to submit it with.

        :raises ValueError: if the task is of a kind that has no way to run here, which a kind added to the
            declaration without one would be.
        """
        if isinstance(task, SubgraphTask):
            return GraphProcess, GraphProcess.launch_inputs(task.body, inputs)

        if isinstance(task, ProcessTask):
            return task.spec.process_class, inputs

        raise ValueError(f'`{task.name}` is of kind `{task.kind}`, which this version of AiiDA cannot run.')

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

        for output, source in self.graph.outputs.items():
            if source.task is None:
                # The graph passes one of its own inputs on, so the value is already there and nothing produced it.
                self.out(output, given[source.port])
                continue

            if source.task in self._skipped:
                self.report(f'output `{output}` is not returned, since `{source.task}` did not run')
                continue

            if not isinstance(self.graph.task(source.task), MapTask):
                self.out(output, load_node(self._done[source.task]).outputs[source.port])
                continue

            # A map produced a result per item, so the output is a namespace holding one entry per item.
            for instance in self._instances[source.task]:
                self.out(
                    f'{output}.{self._item_key(source.task, instance)}',
                    load_node(self._done[instance]).outputs[source.port],
                )

        return None
