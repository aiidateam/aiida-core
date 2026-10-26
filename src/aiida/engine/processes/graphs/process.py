###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Execute static graphs and Python-valued task functions on the process engine."""

from __future__ import annotations

import functools
import typing as t
from collections.abc import MutableMapping

from aiida.common.exceptions import GraphTypeCheckError
from aiida.common.extendeddicts import AttributesFrozendict
from aiida.common.lang import override
from aiida.common.processes import ProcessState
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.graphs.ir import GraphIR, ProcessTask
from aiida.engine.processes.graphs.run import GraphRun, GraphRunState, Start
from aiida.engine.processes.ports import PortNamespace
from aiida.engine.processes.process import Process
from aiida.engine.processes.process_spec import GraphProcessSpec, ProcessSpec
from aiida.engine.processes.states import Wait
from aiida.orm import Dict, GraphNode

__all__ = ('GraphProcess',)


class GraphProcess(Process):
    """Dispatch the runs chosen by GraphRun and return their existing data nodes."""

    _node_class = GraphNode
    _spec_class = GraphProcessSpec
    _GRAPH = 'graph'
    _GRAPH_INPUTS = 'graph_inputs'

    @classmethod
    def define(cls, spec: ProcessSpec) -> None:  # type: ignore[override]
        """Declare the stored graph and its per-instance inputs namespace."""
        super().define(spec)
        spec.input(cls._GRAPH, valid_type=Dict)
        # The stored graph supplies the fixed contract for these per-instance ports.
        spec.input_namespace(cls._GRAPH_INPUTS, dynamic=True, required=False)
        spec.outputs.dynamic = True
        spec.exit_code(400, 'ERROR_TASK_FAILED', message='The task `{task}` did not finish successfully.')

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self._run: GraphRun | None = None
        self._saved: GraphRunState = {}
        self._watched_pks: set[int] = set()
        super().__init__(*args, **kwargs)

    @override
    def _create_and_setup_db_record(self) -> t.Any:
        graph = GraphIR.from_dict(self.inputs[self._GRAPH].get_dict())
        stored = graph.serialize_inputs(dict(self.inputs.get(self._GRAPH_INPUTS, {})))
        self._input_sources = AttributesFrozendict({**self._input_sources, self._GRAPH_INPUTS: stored})
        self._parsed_inputs = AttributesFrozendict(
            {**self.inputs, self._GRAPH_INPUTS: graph.build_input_namespace().prepare(stored).runtime}
        )
        self._run = GraphRun.from_dict(graph=graph, given=stored, data=self._saved)
        return super()._create_and_setup_db_record()

    @classmethod
    def _launch_inputs(cls, body: GraphIR, inputs: dict[str, t.Any]) -> dict[str, t.Any]:
        """Fill graph arguments."""
        return {cls._GRAPH: Dict(dict=body.to_dict()), cls._GRAPH_INPUTS: body.prepare_inputs(inputs)}

    @property
    @override
    def output_ports(self) -> PortNamespace:
        """Return the static outputs declared by the stored graph."""
        return self._graph.build_output_namespace()

    @property
    def _run_state(self) -> GraphRun:
        """Return the scheduling progress, rebuilt from the checkpoint when needed."""
        if self._run is None:
            graph = GraphIR.from_dict(self.inputs[self._GRAPH].get_dict())
            self._run = GraphRun.from_dict(
                graph=graph,
                given=graph.serialize_inputs(dict(self._input_sources.get(self._GRAPH_INPUTS, {}))),
                data=self._saved,
            )
        return self._run

    @property
    def _graph(self) -> GraphIR:
        """Return the static graph this process executes."""
        return self._run_state.graph

    @override
    def save_instance_state(self, out_state: MutableMapping[str, t.Any], save_context: t.Any) -> None:
        """Checkpoint the scheduling progress and the graph input sources."""
        super().save_instance_state(out_state, save_context)
        out_state['run'] = self._run_state.to_dict()
        out_state['graph_input_sources'] = self._encode_input_args(
            dict(self._input_sources.get(self._GRAPH_INPUTS, {}))
        )

    @override
    def load_instance_state(self, saved_state: MutableMapping[str, t.Any], load_context: t.Any) -> None:
        """Restore the scheduling progress and the graph input sources."""
        super().load_instance_state(saved_state, load_context)
        self._run = None
        self._watched_pks = set()
        self._saved = t.cast(GraphRunState, dict(saved_state.get('run', {})))
        if 'graph_input_sources' in saved_state:
            self._input_sources = AttributesFrozendict(
                {**self._input_sources, self._GRAPH_INPUTS: self._decode_input_args(saved_state['graph_input_sources'])}
            )
        self._parsed_inputs = AttributesFrozendict(
            {
                **self.inputs,
                self._GRAPH_INPUTS: self._graph.build_input_namespace()
                .prepare(self._input_sources[self._GRAPH_INPUTS])
                .runtime,
            }
        )

    @override
    async def run(self) -> t.Any:
        """Dispatch one scheduling step; the engine resumes this until no tasks pend."""
        return self._do_step()

    def _do_step(self) -> t.Any:
        """Dispatch the ready tasks, then wait for them or finish the graph."""
        step = self._run_state.step()
        for start in step.starts:
            self._submit(start)
        if self._run_state.pending:
            return Wait(self._do_step, 'waiting for dispatched tasks')
        return self._finish()

    def _submit(self, start: Start) -> None:
        """Submit one task instance as a child process with an explicit call link."""
        process_class: type[Process]
        if start.body is not None:
            process_class, inputs = GraphProcess, self._launch_inputs(start.body, start.inputs)
        elif isinstance(start.task, ProcessTask):
            process_class, inputs = start.task.spec.process_class, start.inputs
        else:
            msg = f'unsupported task `{start.task.name}`.'
            raise GraphTypeCheckError(msg)
        metadata = {**inputs.get('metadata', {}), 'call_link_label': start.instance}
        node = self.submit(process_class, **{**inputs, 'metadata': metadata})
        assert node.pk is not None
        self._run_state.started(start.instance, node.pk)
        self.report(f'dispatched task `{start.instance}` as {node.pk}')

    @override
    def on_wait(self, awaitables: t.Sequence[t.Awaitable]) -> None:
        """Resume this process when any dispatched task finishes."""
        super().on_wait(awaitables)
        self._watch_pending()

    def _watch_pending(self) -> None:
        """Register one finish callback per pending task."""
        for instance, pk in self._run_state.pending.items():
            if pk in self._watched_pks:
                continue
            self._watched_pks.add(pk)
            self.runner.call_on_process_finish(
                pk, functools.partial(self.call_soon, self._on_task_finished, instance, pk)
            )

    def _on_task_finished(self, instance: str, pk: int) -> None:
        """Record one finished task instance and resume a waiting graph."""
        self._run_state.completed(instance, pk)
        if self.state == ProcessState.WAITING:
            self.resume()

    def _finish(self) -> ExitCode | None:
        """Return the task failure exit code, or expose the graph outputs."""
        state = self._run_state
        if state.failed:
            return self.exit_codes.ERROR_TASK_FAILED.format(task=state.failed[0])
        for name, value in state.outputs().items():
            self.out(name, value)
        return None

    @override
    def _build_process_label(self) -> str:
        return self._graph.identifier or super()._build_process_label()
