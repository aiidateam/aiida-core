###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Execute static graphs with one process owning every nested scope."""

from __future__ import annotations

import functools
import json
import typing as t
from collections.abc import Mapping, MutableMapping

from typing_extensions import NotRequired

from aiida.common.exceptions import GraphRuntimeError, GraphTypeCheckError, GraphValidationError
from aiida.common.extendeddicts import AttributesFrozendict
from aiida.common.lang import override
from aiida.common.links import LinkType
from aiida.common.processes import ProcessState
from aiida.engine.execution import RetryPolicy
from aiida.engine.processes.calcjobs.calcjob import CalcJob
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.generic.ports import UNSPECIFIED, Port
from aiida.engine.processes.generic.ports import PortNamespace as GenericPortNamespace
from aiida.engine.processes.graphs.inputs import _at, _place, _prepare_graph_inputs
from aiida.engine.processes.graphs.ir import GraphIR, InlineOperation, MapControl, ProcessTask, _input_ports_at
from aiida.engine.processes.graphs.par_map import _collect_dict, _collect_list
from aiida.engine.processes.graphs.preview import GraphLaunchPreview, _preview
from aiida.engine.processes.graphs.recovery import (
    _OOM,
    _at_placement,
    _bind_execution_policy,
    _decode_policy,
    _policy_error,
    _validate_attempt,
)
from aiida.engine.processes.graphs.run import GraphRun, _GraphRunState, _Start
from aiida.engine.processes.graphs.runtime_config import (
    _bind_runtime_config,
    _merge_runtime_inputs,
    _runtime_placements,
)
from aiida.engine.processes.graphs.tasks import TaskProcess
from aiida.engine.processes.ports import PORT_NAMESPACE_SEPARATOR, PortNamespace, _runtime_value, checkpoint_leaves
from aiida.engine.processes.process import Process
from aiida.engine.processes.process_spec import GraphProcessSpec, ProcessSpec
from aiida.engine.processes.states import Wait
from aiida.orm import CalcJobNode, Dict, GraphNode, Node, ProcessNode, load_node, to_aiida_type
from aiida.orm.nodes.data.container import detach_owned_inputs_and_copies

__all__ = ('GraphProcess',)


def _store_run_nodes(data: t.Any) -> None:
    """Store every unstored node in checkpointable run state, without adding provenance links.

    Scope values and launch configuration may contain ORM nodes without provenance links.
    Standalone storage keeps them YAML-serializable for checkpoints.
    """
    if isinstance(data, Node):
        if not data.is_stored:
            data.store()
    elif isinstance(data, Mapping):
        for value in data.values():
            _store_run_nodes(value)
    elif isinstance(data, (list, tuple)):
        for value in data:
            _store_run_nodes(value)


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


class _RecoveryState(t.TypedDict):
    path: tuple[str, ...]
    inputs: dict[str, t.Any]
    number: int
    effective_kb: int
    scope: NotRequired[str]


def _snapshot_protocol(record: Mapping[str, t.Any]) -> dict[str, t.Any]:
    if not record:
        return {}
    if (
        record.keys() == {'protocol', 'version', 'overrides'}
        and all(isinstance(record[key], str) and record[key].strip() for key in ('protocol', 'version'))
        and isinstance(record['overrides'], Mapping)
    ):
        try:
            return json.loads(json.dumps({**record, 'overrides': dict(record['overrides'])}, allow_nan=False))
        except (ValueError, TypeError) as exc:
            msg = 'protocol overrides must be JSON-compatible.'
            raise GraphValidationError(msg) from exc
    msg = 'expected a protocol identifier, nonempty version, and mapping of explicit overrides.'
    raise GraphValidationError(msg)


class GraphProcess(Process):
    """Dispatch the runs chosen by GraphRun and return their existing data nodes."""

    _node_class = GraphNode
    _spec_class = GraphProcessSpec
    _GRAPH = 'graph'
    _GRAPH_INPUTS = 'graph_inputs'
    _RUNTIME_CONFIG = 'runtime_config'
    _EXECUTION_POLICY = 'execution_policy'
    _PROTOCOL_RECORD = 'protocol_record'

    @classmethod
    def define(cls, spec: ProcessSpec) -> None:  # type: ignore[override]
        """Declare the engine launch envelope, distinct from the scientific input links."""
        super().define(spec)
        spec.input(cls._GRAPH, valid_type=Dict)
        # The stored graph supplies the fixed contract for these per-instance ports.
        spec.input_namespace(cls._GRAPH_INPUTS, dynamic=True, required=False)
        spec.input_namespace(cls._RUNTIME_CONFIG, dynamic=True, required=False, non_db=True)
        spec.input_namespace(cls._EXECUTION_POLICY, dynamic=True, required=False, non_db=True)
        spec.input_namespace(cls._PROTOCOL_RECORD, dynamic=True, required=False, non_db=True)
        spec.outputs.dynamic = True
        spec.exit_code(400, 'ERROR_TASK_FAILED', message='The task `{task}` did not finish successfully.')
        spec.exit_code(401, 'ERROR_GRAPH_RUNTIME', message='The graph failed: {message}.')

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self._run: GraphRun | None = None
        self._saved: _GraphRunState = {}
        self._scope_nodes: dict[str, GraphNode] = {}
        self._watched_pks: set[int] = set()
        self._recovery: dict[str, _RecoveryState] = {}
        self._finished_attempts: set[tuple[str, int]] = set()
        super().__init__(*args, **kwargs)

    @override
    def _create_and_setup_db_record(self) -> t.Any:
        graph = GraphIR.from_dict(self.inputs[self._GRAPH].get_dict())
        self._validate_root_outputs(graph)
        stored = _serialize_graph_inputs(graph, dict(self.inputs.get(self._GRAPH_INPUTS, {})))
        # Checkpoint the normalized containers, not the unstored members they copied.
        self._raw_inputs = AttributesFrozendict({**(self.raw_inputs or {}), self._GRAPH_INPUTS: stored})
        self._input_sources = AttributesFrozendict({**self._input_sources, self._GRAPH_INPUTS: stored})
        self._parsed_inputs = AttributesFrozendict(
            {**self.inputs, self._GRAPH_INPUTS: graph.build_input_namespace().prepare(stored).runtime}
        )
        config = _bind_runtime_config(graph, self.inputs.get(self._RUNTIME_CONFIG, {}))
        policy = _bind_execution_policy(graph, config, self.inputs.get(self._EXECUTION_POLICY, {}), from_snapshot=True)
        protocol = _snapshot_protocol(self.inputs.get(self._PROTOCOL_RECORD, {}))
        _store_run_nodes(config)
        envelope = {self._RUNTIME_CONFIG: config, self._EXECUTION_POLICY: policy, self._PROTOCOL_RECORD: protocol}
        self._input_sources = AttributesFrozendict({**self._input_sources, **envelope})
        self._parsed_inputs = AttributesFrozendict({**self.inputs, **envelope})
        self._run = GraphRun.from_dict(graph=graph, given=stored, data=self._saved)
        return super()._create_and_setup_db_record()

    @override
    def _flat_inputs(self) -> dict[str, t.Any]:
        """Link workflow arguments under their declared names, not the launch envelope."""
        return dict(
            super()._flatten_inputs(self._graph.build_input_namespace(), self._input_sources[self._GRAPH_INPUTS])
        )

    @override
    def _setup_db_record(self) -> None:
        super()._setup_db_record()
        self.node.base.attributes.set(GraphNode.GRAPH_DEFINITION_KEY, self.inputs[self._GRAPH].get_dict())
        checkpoint_inputs = tuple(checkpoint_leaves(self._graph.build_input_namespace()))
        if checkpoint_inputs:
            self.node.base.attributes.set('checkpoint_ports', {'inputs': checkpoint_inputs})
        config = self._input_sources.get(self._RUNTIME_CONFIG, {})
        if config:
            self.node.base.attributes.set(GraphNode.RUNTIME_CONFIG_KEY, super()._encode_input_args(dict(config)))
        for key, channel in (
            (GraphNode.EXECUTION_POLICY_KEY, self._EXECUTION_POLICY),
            (GraphNode.PROTOCOL_KEY, self._PROTOCOL_RECORD),
        ):
            if snapshot := self._input_sources.get(channel):
                self.node.base.attributes.set(key, snapshot)

    @staticmethod
    def _validate_root_outputs(body: GraphIR) -> None:
        if body.checkpoint_outputs:
            msg = f'root graph outputs cannot be checkpoint-only: {list(body.checkpoint_outputs)}.'
            raise GraphValidationError(msg)

    @classmethod
    def _launch_inputs(
        cls,
        body: GraphIR,
        inputs: dict[str, t.Any],
        runtime_config: Mapping[str, t.Any] | None = None,
        execution_policy: object = UNSPECIFIED,
        protocol_record: Mapping[str, t.Any] | None = None,
    ) -> dict[str, t.Any]:
        """Fill workflow arguments and bind execution configuration separately."""
        cls._validate_root_outputs(body)
        prepared = _prepare_graph_inputs(body.build_input_namespace(), inputs, body.identifier)
        config = _bind_runtime_config(body, {} if runtime_config is None else runtime_config)
        return {
            cls._GRAPH: Dict(dict=body.to_dict()),
            cls._GRAPH_INPUTS: prepared,
            cls._RUNTIME_CONFIG: config,
            cls._EXECUTION_POLICY: _bind_execution_policy(
                body, config, {} if execution_policy is UNSPECIFIED else execution_policy
            ),
            cls._PROTOCOL_RECORD: _snapshot_protocol(protocol_record or {}),
        }

    @classmethod
    def preview_launch(cls, body: GraphIR, launch: Mapping[str, t.Any]) -> GraphLaunchPreview:
        """Validate graph inputs and inspect a prepared launch without creating a process."""
        inputs = _serialize_graph_inputs(body, launch[cls._GRAPH_INPUTS])
        return _preview(body, inputs, launch[cls._RUNTIME_CONFIG], launch[cls._EXECUTION_POLICY])

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
    def _encode_input_args(self, inputs: dict[str, t.Any]) -> dict[str, t.Any] | str:
        if self._graph.has_checkpoint_ports:
            return dict(inputs)
        return super()._encode_input_args(inputs)

    @override
    def save_instance_state(self, out_state: MutableMapping[str, t.Any], save_context: t.Any) -> None:
        """Checkpoint the scheduling progress and the graph input sources."""
        # The launch envelope remains checkpointed, but no longer has scientific input links.
        _store_run_nodes(self._input_sources[self._GRAPH])
        _store_run_nodes(self._input_sources.get(self._RUNTIME_CONFIG))
        super().save_instance_state(out_state, save_context)
        run_state = self._run_state.to_dict()
        # Durable scope values are ORM references; checkpoint-only values stay in the payload.
        _store_run_nodes(run_state)
        out_state['run'] = self._encode_input_args(t.cast(dict[str, t.Any], run_state))
        if self._recovery:
            _store_run_nodes(self._recovery)
            out_state['recovery'] = self._encode_input_args(self._recovery)
        out_state['graph_input_sources'] = self._encode_input_args(
            dict(self._input_sources.get(self._GRAPH_INPUTS, {}))
        )

    @override
    def load_instance_state(self, saved_state: MutableMapping[str, t.Any], load_context: t.Any) -> None:
        """Restore the scheduling progress and the graph input sources."""
        super().load_instance_state(saved_state, load_context)
        self._run = None
        self._scope_nodes = {}
        self._watched_pks = set()
        self._finished_attempts = set()
        self._recovery = self._decode_input_args(saved_state['recovery']) if 'recovery' in saved_state else {}
        saved_run = saved_state.get('run', {})
        if isinstance(saved_run, str):
            saved_run = self._decode_input_args(saved_run)
        self._saved = t.cast(_GraphRunState, dict(saved_run))
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
        finished, self._finished_attempts = self._finished_attempts, set()
        for instance, pk in sorted(finished):
            self._settle_attempt(instance, pk)
        try:
            step = self._run_state.step(sync_scopes=self._sync_scope_nodes if self.node.is_stored else None)
        except GraphRuntimeError as exc:
            return self.exit_codes.ERROR_GRAPH_RUNTIME.format(message=str(exc))
        for start in step.starts:
            self._submit(start)

        if self._run_state.pending:
            return Wait(self._do_step, 'waiting for dispatched tasks')
        return self._finish()

    def _scope_owner(self, key: str) -> tuple[ProcessNode, str]:
        """Return the nearest graph node and its prefix in the scheduler's label space."""
        scopes = self._run_state.scopes
        while True:
            scope = scopes[key]
            if self.node.is_stored and scope['kind'] in ('subgraph', 'map'):
                if key not in self._scope_nodes:
                    self._scope_nodes[key] = self._enter_scope(key)
                return self._scope_nodes[key], scope['prefix']
            if (parent := scope['parent']) is None:
                return self.node, ''
            key = parent

    @staticmethod
    def _called_at(caller: ProcessNode, label: str) -> ProcessNode | None:
        links = caller.base.links.get_outgoing(
            link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK), link_label_filter=label
        )
        for entry in links:
            if entry.link_label == label:
                assert isinstance(entry.node, ProcessNode)
                return entry.node
        return None

    def _enter_scope(self, key: str) -> GraphNode:
        """Record an explicit invocation without creating another engine process."""
        state = self._run_state
        scope = state.scopes[key]
        parent = scope['parent']
        assert parent is not None
        caller, prefix = self._scope_owner(parent)
        label = scope['prefix'].removeprefix(prefix).removesuffix('__')
        graph = state._template_of(key)
        ports = graph.build_input_namespace()
        given = scope['given']
        node = self._called_at(caller, label)
        if node is None:
            node = GraphNode(backend=self.node.backend)
            node.set_process_type(self.build_process_type())
            node.set_process_label(graph.identifier or label)
            node.set_process_state(ProcessState.RUNNING)
            node.base.attributes.set_many(
                {GraphNode.GRAPH_DEFINITION_KEY: graph.to_dict(), GraphNode.EXECUTOR_UUID_KEY: self.node.uuid}
            )
            checkpoint = {
                name: paths
                for name, namespace in (('inputs', ports), ('outputs', graph.build_output_namespace()))
                if (paths := tuple(checkpoint_leaves(namespace)))
            }
            if checkpoint:
                node.base.attributes.set('checkpoint_ports', checkpoint)
            self._record_scope_configuration(node, graph, state._config_prefix(key))
            node.base.links.add_incoming(caller, LinkType.CALL_WORK, label)
            serialized = ports.serialize(detach_owned_inputs_and_copies(given)[0])
            for name, value in self._flatten_inputs(ports, serialized or {}):
                if value is not None:
                    node.base.links.add_incoming(value, LinkType.INPUT_WORK, name)
            node.store_all()
        assert isinstance(node, GraphNode)
        for entry in node.base.links.get_incoming(link_type=LinkType.INPUT_WORK):
            _place(given, entry.link_label.replace(PORT_NAMESPACE_SEPARATOR, '.'), entry.node)
        return node

    def _record_scope_configuration(self, node: GraphNode, graph: GraphIR, prefix: tuple[str, ...]) -> None:
        for attr, channel in (
            (GraphNode.RUNTIME_CONFIG_KEY, self._RUNTIME_CONFIG),
            (GraphNode.EXECUTION_POLICY_KEY, self._EXECUTION_POLICY),
        ):
            source = _at_placement(self.inputs.get(channel, {}), prefix)
            if not source:
                continue
            # Maps share their enclosing configuration namespace with other placements.
            snapshot: dict[str, t.Any] = {}
            for path, _, _ in _runtime_placements(graph):
                if settings := _at_placement(source, path):
                    _place(snapshot, '.'.join(path), settings)
            if snapshot:
                node.base.attributes.set(
                    attr, super()._encode_input_args(snapshot) if channel == self._RUNTIME_CONFIG else snapshot
                )

    def _sync_scope_nodes(self) -> None:
        """Enter scopes before dispatch and publish outputs before dependents consume them."""
        state = self._run_state
        keys = [key for key, scope in state.scopes.items() if scope['kind'] in ('subgraph', 'map')]
        for key in keys:
            if key not in self._scope_nodes:
                self._scope_nodes[key] = self._enter_scope(key)
        for key in reversed(keys):
            if key in state.recorded_outputs:
                continue
            node = self._scope_nodes[key]
            if state._scope_ok(key):
                state.recorded_outputs[key] = self._publish_scope_outputs(key, node)
            elif not node.is_sealed and (exit_code := state.scope_exit_code(key)) is not None:
                self._finish_scope(node, exit_code)

    def _publish_scope_outputs(self, key: str, node: GraphNode) -> dict[str, t.Any]:
        """Record durable outputs, keeping checkpoint-only values in the scheduler."""
        state = self._run_state
        outputs = state._scope_outputs(key)
        ports = state._template_of(key).build_output_namespace()
        checkpoint = {path.replace('.', PORT_NAMESPACE_SEPARATOR) for path in checkpoint_leaves(ports)}
        recorded = {entry.link_label: entry.node for entry in node.base.links.get_outgoing(link_type=LinkType.RETURN)}
        with node.backend.transaction():
            for label, value in self._flatten_outputs(ports, outputs):
                if label in checkpoint:
                    continue
                path = label.replace(PORT_NAMESPACE_SEPARATOR, '.')
                if label not in recorded:
                    output = self._materialize_output(ports.get_port(path), value)
                    self._reject_owned_workflow_output(output)
                    if not output.is_stored:
                        output.base.links.add_incoming(node, LinkType.CREATE, label)
                        output.store()
                    output.base.links.add_incoming(node, LinkType.RETURN, label)
                    recorded[label] = output
                _place(outputs, path, recorded[label])
            if not node.is_sealed:
                self._finish_scope(node, ExitCode())
        return outputs

    @staticmethod
    def _finish_scope(node: GraphNode, exit_code: ExitCode) -> None:
        node.set_exit_status(exit_code.status)
        node.set_exit_message(exit_code.message)
        node.set_process_state(ProcessState.FINISHED)
        node.seal()

    def _submit(self, start: _Start) -> None:
        """Submit one task under the graph invocation that owns it."""
        process_class: type[Process]
        if isinstance(start.task, ProcessTask):
            process_class, inputs = start.task.spec.process_class, start.inputs
        elif isinstance(start.task, MapControl):
            process_class, inputs = self._collector_for(start.task, start.inputs)
        elif isinstance(start.task, InlineOperation):
            msg = (
                f'inline operation `{start.task.name}` evaluates inside the graph run; '
                'it must never dispatch a child process.'
            )
            raise GraphRuntimeError(msg)
        else:
            msg = f'unsupported task `{start.task.name}`.'
            raise GraphTypeCheckError(msg)
        if isinstance(start.task, ProcessTask):
            configured = _at_placement(self.inputs.get(self._RUNTIME_CONFIG, {}), start.config_path)
            inputs = _merge_runtime_inputs(start.task, configured, inputs)
            if policy := self._policy_at(start.config_path):
                assert issubclass(process_class, CalcJob)
                try:
                    effective = _validate_attempt(process_class, inputs, policy)
                except ValueError as exc:
                    raise _policy_error(start.config_path, str(exc)) from exc
                state = _RecoveryState(
                    path=start.config_path, inputs=inputs, number=1, effective_kb=effective, scope=start.scope
                )
                self._dispatch_attempt(start.instance, process_class, state)
                return
        caller, prefix = self._scope_owner(start.scope)
        label = start.instance.removeprefix(prefix)
        metadata = {**inputs.get('metadata', {}), 'call_link_label': label}
        checkpoint_task = issubclass(process_class, TaskProcess) and bool(process_class.checkpoint_ports())
        if checkpoint_task:
            metadata['disable_cache'] = True
        node = self._called_at(caller, label) if checkpoint_task or prefix else None
        if node is None:
            node = self._submit_for(caller, process_class, {**inputs, 'metadata': metadata})
        assert node.pk is not None
        self._run_state.started(start.instance, node.pk)
        self.report(f'dispatched task `{start.instance}` as {node.pk}')

    def _submit_for(self, caller: ProcessNode, process: type[Process], inputs: dict[str, t.Any]) -> ProcessNode:
        if caller is self.node:
            return self.submit(process, inputs)
        assert caller.pk is not None
        with self._call_as(caller.pk):
            return self.submit(process, inputs)

    def _graph_calls(self) -> t.Iterator[tuple[ProcessNode, bool]]:
        """Walk calls through inline scope nodes, but not through independently scheduled children."""
        pending = list(self.node.called)
        while pending:
            child = pending.pop()
            inline = (
                isinstance(child, GraphNode)
                and child.base.attributes.get(GraphNode.EXECUTOR_UUID_KEY, None) == self.node.uuid
            )
            yield child, inline
            if inline:
                pending.extend(child.called)

    @override
    def _active_called_processes(self) -> list[ProcessNode]:
        return [child for child, inline in self._graph_calls() if not inline and not child.is_terminated]

    @override
    def on_terminated(self) -> None:
        if self.node.is_stored:
            for child, inline in self._graph_calls():
                if not inline or child.is_sealed:
                    continue
                assert isinstance(child, GraphNode)
                if self.node.is_failed:
                    exit_code = ExitCode(self.node.exit_status or 0, self.node.exit_message)
                    self._finish_scope(child, exit_code)
                else:
                    if (exception := self.node.exception) is not None:
                        child.set_exception(exception)
                    process_state = self.node.process_state
                    assert process_state is not None
                    child.set_process_state(ProcessState.KILLED if self.node.is_finished else process_state)
                    child.seal()
        super().on_terminated()
        if not self._enable_persistence and self.node.is_stored and self._graph.has_checkpoint_ports:
            self.node.backend.checkpoint_store.discard_all(node_uuid=self.node.uuid)

    def _policy_at(self, path: tuple[str, ...]) -> RetryPolicy | None:
        snapshot = _at_placement(self.inputs.get(self._EXECUTION_POLICY, {}), path)
        return _decode_policy(snapshot) if snapshot else None

    def _dispatch_attempt(self, instance: str, process_class: type[CalcJob], state: _RecoveryState) -> None:
        number = state['number']
        scope = state.get('scope')
        caller, prefix = self._scope_owner(scope) if scope is not None else (self.node, '')
        label = f'graph_attempt_{number}__{instance.removeprefix(prefix)}'
        # A child may already have been submitted after the most recent checkpoint.
        child = self._called_at(caller, label)
        if child is None:
            inputs = state['inputs']
            metadata = {**inputs.get('metadata', {}), 'call_link_label': label}
            child = self._submit_for(caller, process_class, {**inputs, 'metadata': metadata})
        assert isinstance(child, CalcJobNode) and child.pk is not None
        self._recovery[instance] = state
        self._run_state.started(instance, child.pk)
        self._record_attempt(instance, child, state)
        self.report(f'task `{instance}` attempt {number}: child {child.pk} (memory {state["effective_kb"]} kB)')

    def _record_attempt(self, instance: str, child: CalcJobNode, state: _RecoveryState, **decision: t.Any) -> None:
        attempts = self.node.base.attributes.get(GraphNode.ATTEMPTS_KEY, {})
        history = attempts.setdefault(instance, [])
        index = state['number'] - 1
        if index == len(history):
            history.append(
                {
                    'child_uuid': child.uuid,
                    'placement': list(state['path']),
                    'attempt': state['number'],
                    'effective_memory_kb': state['effective_kb'],
                    'execution_options': child.get_options(),
                }
            )
        if decision:
            history[index].update(decision)
        self.node.base.attributes.set(GraphNode.ATTEMPTS_KEY, attempts)

    def _settle_attempt(self, instance: str, pk: int) -> None:
        """Retry in process scope before exposing a terminal outcome to GraphRun."""
        if self._run_state.pending.get(instance) != pk:
            return
        state = self._recovery[instance]
        policy = self._policy_at(state['path'])
        assert policy is not None
        child = load_node(pk)
        assert isinstance(child, CalcJobNode)
        classification = child.base.attributes.get(CalcJobNode.SCHEDULER_FAILURE_KEY, None) if child.is_failed else None
        decision: dict[str, t.Any] = {'failure': classification, 'decision': 'terminal'}
        if classification == _OOM.value and state['number'] < policy.max_attempts:
            inputs = state['inputs']
            metadata = inputs.get('metadata', {})
            options = metadata.get('options', {})
            memory = policy.on[_OOM]._next_request(options['max_memory_kb'])
            candidate = {**inputs, 'metadata': {**metadata, 'options': {**options, 'max_memory_kb': memory}}}
            process_class = child.process_class
            assert issubclass(process_class, CalcJob)
            try:
                effective = _validate_attempt(process_class, candidate, policy)
            except ValueError as exc:
                decision['reason'] = str(exc)
            else:
                if effective > state['effective_kb']:
                    self._record_attempt(instance, child, state, failure=classification, decision='increase_memory')
                    self._dispatch_attempt(
                        instance,
                        process_class,
                        {
                            **state,
                            'number': state['number'] + 1,
                            'inputs': candidate,
                            'effective_kb': effective,
                        },
                    )
                    return
                decision['reason'] = 'no effective increase within the memory ceiling'
        elif classification == _OOM.value:
            decision['reason'] = 'attempt budget exhausted'
        self._record_attempt(instance, child, state, **decision)
        del self._recovery[instance]
        self._run_state.completed(instance, pk)

    def _collector_for(self, task: MapControl, inputs: dict[str, t.Any]) -> tuple[type[Process], dict[str, t.Any]]:
        """Return the collector creating one map's result container from its item outputs.

        The collector is a calculation, so the result container carries a `CREATE` link from it
        while the graph only ever returns that existing container.
        """
        collected = _collect_list if task.container == 'list' else _collect_dict
        return collected.process_class, dict(inputs)

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
        if instance in self._recovery:
            self._finished_attempts.add((instance, pk))
        else:
            self._run_state.completed(instance, pk)
        if self.state == ProcessState.WAITING:
            self.resume()

    def _finish(self) -> ExitCode | None:
        """Return a task or runtime failure exit code, or expose the graph outputs."""
        state = self._run_state
        if (exit_code := state.propagated_exit_code) is not None:
            return exit_code
        if failures := state.failures():
            failure = failures[0]
            if failure.items:
                for instance in failure.items:
                    self.report(f'map `{failure.label}` item `{instance}` did not finish successfully')
            if failure.missing:
                self.report(f'task `{failure.label}` finished without its declared outputs {list(failure.missing)}')
            for message in failure.mistyped:
                self.report(f'task `{failure.label}` {message}')
            return self.exit_codes.ERROR_TASK_FAILED.format(task=failure.label)
        try:
            for name, value in state.outputs().items():
                self.out(name, self._materialize_output(self.output_ports[name], value))
        except GraphRuntimeError as exc:
            return self.exit_codes.ERROR_GRAPH_RUNTIME.format(message=str(exc))
        return None

    def _materialize_output(self, port: Port | GenericPortNamespace, value: t.Any) -> t.Any:
        """Convert inline output values to nodes without changing existing node identity."""
        if isinstance(port, GenericPortNamespace):
            return {name: self._materialize_output(port[name], child) for name, child in value.items()}
        if isinstance(value, Node):
            return value
        converted = _runtime_value(port.valid_type, value)
        return converted if isinstance(converted, Node) else to_aiida_type(converted)

    @override
    def _build_process_label(self) -> str:
        if self._graph.identifier:
            return self._graph.identifier
        # Control-flow children carry no identifier; they take the placement name they were dispatched under.
        label = (self.inputs.get('metadata', {}) or {}).get('call_link_label')
        if self.get_parent_calc() is not None and isinstance(label, str) and label:
            return label
        return super()._build_process_label()
