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
from collections.abc import Mapping, MutableMapping

from aiida.common.exceptions import GraphTypeCheckError, GraphValidationError
from aiida.common.extendeddicts import AttributesFrozendict
from aiida.common.lang import override
from aiida.common.processes import ProcessState
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.graphs.inputs import _at, _prepare_graph_inputs
from aiida.engine.processes.graphs.ir import GraphIR, ProcessTask, _input_ports_at
from aiida.engine.processes.graphs.run import GraphRun, _GraphRunState, _Start
from aiida.engine.processes.graphs.tasks import _merge_task_metadata, _needs_metadata
from aiida.engine.processes.ports import PortNamespace
from aiida.engine.processes.process import Process
from aiida.engine.processes.process_spec import GraphProcessSpec, ProcessSpec
from aiida.engine.processes.states import Wait
from aiida.orm import Dict, GraphNode

__all__ = ('GraphProcess',)


def _serialize_graph_inputs(graph: GraphIR, given: Mapping[str, t.Any]) -> dict[str, t.Any]:
    """Prepare launch inputs and validate them against the graph boundary and every consumer."""
    namespace = graph.build_input_namespace()
    prepared = _prepare_graph_inputs(namespace, given, graph.identifier)
    serialized = namespace.serialize(prepared)
    if serialized is None:
        msg = 'graph inputs serialized to `None`; expected a mapping.'
        raise GraphValidationError(msg)
    runtime = namespace.prepare(serialized).runtime
    assert isinstance(runtime, Mapping)
    error = namespace.validate(runtime)
    if error is not None:
        raise GraphValidationError(error)
    for name, targets in graph.inputs.items():
        try:
            value = _at(serialized, name)
        except KeyError:
            continue
        for task, path in targets:
            for port in _input_ports_at(graph.task(task), path):
                error = port.validate(port.prepare(value).runtime)
                if error is not None:
                    raise GraphValidationError(error)
    return serialized


class GraphProcess(Process):
    """Dispatch the runs chosen by GraphRun and return their existing data nodes."""

    _node_class = GraphNode
    _spec_class = GraphProcessSpec
    _GRAPH = 'graph'
    _GRAPH_INPUTS = 'graph_inputs'
    _TASK_METADATA = 'task_metadata'

    @classmethod
    def define(cls, spec: ProcessSpec) -> None:  # type: ignore[override]
        """Declare the stored graph and its per-instance inputs namespace."""
        super().define(spec)
        spec.input(cls._GRAPH, valid_type=Dict)
        # The stored graph supplies the fixed contract for these per-instance ports.
        spec.input_namespace(cls._GRAPH_INPUTS, dynamic=True, required=False)
        # Per-placement `CalcJob` metadata, keyed by placement name; never routed as graph inputs.
        spec.input(cls._TASK_METADATA, valid_type=Dict, required=False, is_metadata=False)
        spec.outputs.dynamic = True
        spec.exit_code(400, 'ERROR_TASK_FAILED', message='The task `{task}` did not finish successfully.')

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self._run: GraphRun | None = None
        self._saved: _GraphRunState = {}
        self._watched_pks: set[int] = set()
        self._body_nodes: dict[int, Dict] = {}
        super().__init__(*args, **kwargs)

    @override
    def _create_and_setup_db_record(self) -> t.Any:
        graph = GraphIR.from_dict(self.inputs[self._GRAPH].get_dict())
        stored = _serialize_graph_inputs(graph, dict(self.inputs.get(self._GRAPH_INPUTS, {})))
        self._input_sources = AttributesFrozendict({**self._input_sources, self._GRAPH_INPUTS: stored})
        self._parsed_inputs = AttributesFrozendict(
            {**self.inputs, self._GRAPH_INPUTS: graph.build_input_namespace().prepare(stored).runtime}
        )
        self._run = GraphRun.from_dict(graph=graph, given=stored, data=self._saved)
        return super()._create_and_setup_db_record()

    @classmethod
    def _launch_inputs(
        cls, body: GraphIR, inputs: dict[str, t.Any], task_metadata: Mapping[str, Mapping[str, t.Any]] | None = None
    ) -> dict[str, t.Any]:
        """Fill graph arguments and stash per-placement `CalcJob` metadata."""
        prepared = _prepare_graph_inputs(body.build_input_namespace(), inputs, body.identifier)
        return {
            cls._GRAPH: Dict(dict=body.to_dict()),
            cls._GRAPH_INPUTS: prepared,
            **({cls._TASK_METADATA: Dict(dict=dict(task_metadata))} if task_metadata else {}),
        }

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
                given=_serialize_graph_inputs(graph, dict(self._input_sources.get(self._GRAPH_INPUTS, {}))),
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
        self._body_nodes = {}
        self._saved = t.cast(_GraphRunState, dict(saved_state.get('run', {})))
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
        # A restored `Waiting` state is not re-entered, so `on_wait` does not fire; re-arm the callbacks.
        if self._run_state.pending:
            self._watch_pending()

    @override
    async def run(self) -> t.Any:
        """Dispatch one scheduling step; the engine re-enters `_do_step` until no tasks pend."""
        return self._do_step()

    def _do_step(self) -> t.Any:
        """Dispatch the ready tasks, then wait for them or finish the graph."""
        step = self._run_state.step()
        for start in step.starts:
            self._submit(start)
        if self._run_state.pending:
            return Wait(self._do_step, 'waiting for dispatched tasks')
        return self._finish()

    def _submit(self, start: _Start) -> None:
        """Submit one task instance as a child process with an explicit call link."""
        process_class: type[Process]
        if start.body is not None:
            process_class = GraphProcess
            inputs = self._launch_inputs(start.body, start.inputs, task_metadata=self._stored_task_metadata() or None)
            inputs[self._GRAPH] = self._stored_body(start.body, inputs[self._GRAPH])
        elif isinstance(start.task, ProcessTask):
            process_class, inputs = start.task.spec.process_class, start.inputs
        else:
            msg = f'unsupported task `{start.task.name}`.'
            raise GraphTypeCheckError(msg)
        if _needs_metadata(start.task):
            stored = self._stored_task_metadata()
            inputs = _merge_task_metadata(start.task, stored, inputs)
        metadata = {**inputs.get('metadata', {}), 'call_link_label': start.instance}
        node = self.submit(process_class, **{**inputs, 'metadata': metadata})
        assert node.pk is not None
        self._run_state.started(start.instance, node.pk)
        self.report(f'dispatched task `{start.instance}` as {node.pk}')

    def _stored_body(self, body: GraphIR, declaration: Dict) -> Dict:
        """Return the stored declaration node for a body, storing it on first dispatch.

        Loop iterations redispatch the same body object, so they share one node. Bodies stay
        alive on the run graph, so `id` keys cannot be reused. A restored process resets the
        cache and stores one extra copy at most.
        """
        key: int = id(body)
        if key not in self._body_nodes:
            self._body_nodes[key] = declaration.store()
        return self._body_nodes[key]

    def _stored_task_metadata(self) -> dict[str, t.Any]:
        """Return the launch metadata stashed per placement name."""
        stored = self.inputs.get(self._TASK_METADATA, None)
        return stored.get_dict() if stored is not None else {}

    @override
    def on_wait(self, awaitables: t.Sequence[t.Awaitable]) -> None:
        """Watch the dispatched tasks so their finish resumes this process."""
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
            failed = state.failed[0]
            if missing := state.missing_outputs(failed):
                self.report(f'task `{failed}` finished without its declared outputs {missing}')
            for message in state.mistyped_outputs(failed):
                self.report(f'task `{failed}` {message}')
            return self.exit_codes.ERROR_TASK_FAILED.format(task=failed)
        for name, value in state.outputs().items():
            self.out(name, value)
        return None

    @override
    def _build_process_label(self) -> str:
        if self._graph.identifier:
            return self._graph.identifier
        # Control-flow children carry no identifier; they take the placement name they were dispatched under.
        label = (self.inputs.get('metadata', {}) or {}).get('call_link_label')
        if self.get_parent_calc() is not None and isinstance(label, str) and label:
            return label
        return super()._build_process_label()
