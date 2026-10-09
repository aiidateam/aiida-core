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

from aiida.common.extendeddicts import AttributesFrozendict
from aiida.common.lang import override
from aiida.common.processes import ProcessState
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.functions import FunctionProcess
from aiida.engine.processes.graphs.run import GraphRun, Start
from aiida.engine.processes.graphs.spec import GraphSpec, ProcessTask
from aiida.engine.processes.ports import PortNamespace
from aiida.engine.processes.process import Process
from aiida.engine.processes.process_spec import ProcessSpec
from aiida.engine.processes.states import Wait
from aiida.orm import Data, Dict, GraphNode, to_aiida_type

__all__ = ('GraphProcess', 'TaskProcess')


class TaskProcess(FunctionProcess):
    """Consume declared Python/ORM inputs and create provenance nodes for leaf outputs."""

    NODE_INPUT_TYPES: t.ClassVar[bool] = False

    @override
    def _out_result(self, result: t.Any) -> None:
        outputs = self.spec().outputs
        names = list(outputs)
        values = result if isinstance(result, tuple) else (result,)
        if not names and result is None:
            return
        if len(values) != len(names):
            msg = f'task declares {len(names)} outputs {names} but returned {len(values)} values.'
            raise ValueError(msg)
        stored = {
            name: value if isinstance(value, Data) else to_aiida_type(value)
            for name, value in zip(names, values, strict=True)
        }
        super()._out_result(stored)


class GraphProcess(Process):
    """Dispatch the runs chosen by GraphRun and return their existing data nodes."""

    _node_class = GraphNode
    _GRAPH = 'graph'
    _GRAPH_INPUTS = 'graph_inputs'

    @classmethod
    def define(cls, spec: ProcessSpec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input(cls._GRAPH, valid_type=Dict)
        # The stored graph supplies the fixed contract for these per-instance ports.
        spec.input_namespace(cls._GRAPH_INPUTS, dynamic=True, required=False)
        spec.outputs.dynamic = True
        spec.exit_code(400, 'ERROR_TASK_FAILED', message='The task `{task}` did not finish successfully.')

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self._run: GraphRun | None = None
        self._saved: dict[str, t.Any] = {}
        super().__init__(*args, **kwargs)

    @override
    def _create_and_setup_db_record(self) -> t.Any:
        graph = GraphSpec.from_dict(self.inputs[self._GRAPH].get_dict())
        stored = graph.serialize_inputs(dict(self.inputs.get(self._GRAPH_INPUTS, {})))
        self._input_sources = AttributesFrozendict({**self._input_sources, self._GRAPH_INPUTS: stored})
        self._parsed_inputs = AttributesFrozendict(
            {**self.inputs, self._GRAPH_INPUTS: graph.input_spec().prepare(stored)}
        )
        return super()._create_and_setup_db_record()

    @classmethod
    def launch_inputs(cls, body: GraphSpec, inputs: dict[str, t.Any]) -> dict[str, t.Any]:
        """Validate graph inputs before constructing its process or storing provenance."""
        return {cls._GRAPH: Dict(dict=body.to_dict()), cls._GRAPH_INPUTS: body.serialize_inputs(inputs)}

    @property
    @override
    def output_ports(self) -> PortNamespace:
        return self.graph.output_spec()

    @property
    def run_state(self) -> GraphRun:
        if self._run is None:
            graph = GraphSpec.from_dict(self.inputs[self._GRAPH].get_dict())
            self._run = GraphRun.from_dict(
                graph=graph,
                given=graph.serialize_inputs(dict(self._input_sources.get(self._GRAPH_INPUTS, {}))),
                data=self._saved,
            )
        return self._run

    @property
    def graph(self) -> GraphSpec:
        return self.run_state.graph

    @override
    def save_instance_state(self, out_state: MutableMapping[str, t.Any], save_context: t.Any) -> None:
        super().save_instance_state(out_state, save_context)
        out_state['run'] = self.run_state.to_dict()
        out_state['graph_input_sources'] = self._encode_input_args(
            dict(self._input_sources.get(self._GRAPH_INPUTS, {}))
        )

    @override
    def load_instance_state(self, saved_state: MutableMapping[str, t.Any], load_context: t.Any) -> None:
        super().load_instance_state(saved_state, load_context)
        self._run = None
        self._saved = dict(saved_state.get('run', {}))
        if 'graph_input_sources' in saved_state:
            self._input_sources = AttributesFrozendict(
                {**self._input_sources, self._GRAPH_INPUTS: self._decode_input_args(saved_state['graph_input_sources'])}
            )
        self._parsed_inputs = AttributesFrozendict(
            {
                **self.inputs,
                self._GRAPH_INPUTS: self.graph.input_spec().prepare(self._input_sources[self._GRAPH_INPUTS]),
            }
        )

    @override
    async def run(self) -> t.Any:
        return self._do_step()

    def _do_step(self) -> t.Any:
        step = self.run_state.step()
        for note in step.notes:
            self.report(note)
        for start in step.starts:
            self._submit(start)
        if self.run_state.pending:
            return Wait(self._do_step, 'waiting for dispatched tasks')
        return self._finish()

    def _submit(self, start: Start) -> None:
        process_class: type[Process]
        if start.body is not None:
            process_class, inputs = GraphProcess, self.launch_inputs(start.body, start.inputs)
        elif isinstance(start.task, ProcessTask):
            process_class, inputs = start.task.spec.process_class, start.inputs
        else:
            msg = f'unsupported task `{start.task.name}`.'
            raise ValueError(msg)
        metadata = {**inputs.get('metadata', {}), 'call_link_label': start.instance}
        node = self.submit(process_class, **{**inputs, 'metadata': metadata})
        assert node.pk is not None
        self.run_state.started(start.instance, node.pk)
        self.report(f'dispatched task `{start.instance}` as {node.pk}')

    @override
    def on_wait(self, awaitables: t.Sequence[t.Awaitable]) -> None:
        super().on_wait(awaitables)
        for instance, pk in self.run_state.pending.items():
            self.runner.call_on_process_finish(
                pk, functools.partial(self.call_soon, self._on_task_finished, instance, pk)
            )

    def _on_task_finished(self, instance: str, pk: int) -> None:
        self.run_state.completed(instance, pk)
        if self.state == ProcessState.WAITING:
            self.resume()

    def _finish(self) -> ExitCode | None:
        state = self.run_state
        if state.failed:
            return self.exit_codes.ERROR_TASK_FAILED.format(task=state.failed[0])
        for name, value in state.outputs().items():
            self.out(name, value)
        return None

    @override
    def _build_process_label(self) -> str:
        return self.graph.identifier or super()._build_process_label()
