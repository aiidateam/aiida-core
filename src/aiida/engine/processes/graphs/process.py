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
from aiida.engine.processes.graphs.run import GraphRun, Start
from aiida.engine.processes.graphs.spec import GraphSpec, ProcessTask
from aiida.engine.processes.process import Process
from aiida.engine.processes.process_spec import ProcessSpec
from aiida.engine.processes.states import Wait
from aiida.orm import Data, Dict, WorkChainNode
from aiida.orm.nodes.data.base import to_aiida_type

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


class GraphProcess(Process):
    """Run a graph of tasks, dispatching each as a child process.

    Every run that is ready is submitted, so it is a process in its own right: it gets its own node, its own entry
    in the provenance graph under the name the graph gave it, and it is scheduled like any other process. What to
    run next is decided by :class:`~aiida.engine.processes.graphs.run.GraphRun`, which knows of no engine, so this
    holds the ports, submits what it is told to, waits, and attaches what came out.
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
        self._run: GraphRun | None = None
        self._saved: dict[str, t.Any] = {}

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

    @property
    def run_state(self) -> GraphRun:
        """Return how far the graph has got, read back from the declaration and what was checkpointed."""
        if self._run is None:
            self._run = GraphRun.from_dict(
                graph=GraphSpec.from_dict(self.inputs[self._GRAPH].get_dict()),
                given=dict(self.inputs.get(self._GRAPH_INPUTS, {})),
                data=self._saved,
            )

        return self._run

    @override
    def save_instance_state(self, out_state: MutableMapping[str, t.Any], save_context: t.Any) -> None:
        super().save_instance_state(out_state, save_context)
        out_state['run'] = self.run_state.to_dict()

    @override
    def load_instance_state(self, saved_state: MutableMapping[str, t.Any], load_context: t.Any) -> None:
        super().load_instance_state(saved_state, load_context)
        self._run = None
        self._saved = dict(saved_state.get('run', {}))

    @override
    async def run(self) -> t.Any:
        return self._do_step()

    def _do_step(self) -> t.Any:
        """Start what the graph says to start next, and wait until something finishes."""
        step = self.run_state.step()

        for note in step.notes:
            self.report(note)

        for start in step.starts:
            self._submit(start)

        if self.run_state.pending:
            return Wait(self._do_step, 'waiting for dispatched tasks')

        return self._finish()

    def _submit(self, start: Start) -> None:
        """Submit one run, under the name that its call link carries."""
        process_class, inputs = self._launch(start)
        metadata = {**inputs.get('metadata', {}), 'call_link_label': start.instance}
        node = self.submit(process_class, **{**inputs, 'metadata': metadata})
        assert node.pk is not None
        self.run_state.started(start.instance, node.pk)
        self.report(f'dispatched task `{start.instance}` as {node.pk}')

    @staticmethod
    def _launch(start: Start) -> tuple[type[Process], dict[str, t.Any]]:
        """Return the process that runs one instance, and the inputs to submit it with.

        :raises ValueError: if the task is of a kind that has no way to run here, which a kind added to the
            declaration without one would be.
        """
        if start.body is not None:
            return GraphProcess, GraphProcess.launch_inputs(start.body, start.inputs)

        if isinstance(start.task, ProcessTask):
            return start.task.spec.process_class, start.inputs

        raise ValueError(f'`{start.task.name}` is of kind `{start.task.kind}`, which this version of AiiDA cannot run.')

    @override
    def on_wait(self, awaitables: t.Sequence[t.Awaitable]) -> None:
        """Ask to be woken when a dispatched task finishes.

        The callbacks are registered on entering the wait, so a task that finished while the graph was still
        dispatching is picked up rather than lost.
        """
        super().on_wait(awaitables)

        for instance, pk in self.run_state.pending.items():
            self.runner.call_on_process_finish(
                pk, functools.partial(self.call_soon, self._on_task_finished, instance, pk)
            )

    def _on_task_finished(self, instance: str, pk: int) -> None:
        """Record that a run finished and continue, which is what advances the graph."""
        self.run_state.completed(instance, pk)

        if self.state == ProcessState.WAITING:
            self.resume()

    def _finish(self) -> ExitCode | None:
        """Attach what the graph produced, or report the task that kept it from completing.

        A task that did not finish well leaves everything downstream of it unable to run, so the graph stops with
        the name of that task rather than dispatching a task whose inputs will never exist.
        """
        state = self.run_state

        if state.failed:
            return self.exit_codes.ERROR_TASK_FAILED.format(task=state.failed[0])

        for output, source in self.graph.outputs.items():
            if source.task is not None and source.task in state.skipped:
                self.report(f'output `{output}` is not returned, since `{source.task}` did not run')

        for name, value in state.outputs().items():
            self.out(name, value)

        return None

    @property
    def graph(self) -> GraphSpec:
        """Return the declaration of the graph being run."""
        return self.run_state.graph
