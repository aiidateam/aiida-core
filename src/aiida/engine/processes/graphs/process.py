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

import functools
import typing as t
from collections.abc import Mapping, MutableMapping
from inspect import get_annotations

from aiida.common.extendeddicts import AttributesFrozendict
from aiida.common.lang import override
from aiida.common.processes import ProcessState
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.functions import FunctionProcess
from aiida.engine.processes.graphs.bindings import validate_bound_tasks
from aiida.engine.processes.graphs.handlers import TaskWorkChain, launch_under_namespace
from aiida.engine.processes.graphs.run import GraphRun, Start
from aiida.engine.processes.graphs.spec import GraphSpec, ProcessTask
from aiida.engine.processes.port_model import PortModel, fields_of, is_structured
from aiida.engine.processes.ports import PortNamespace
from aiida.engine.processes.process import Process
from aiida.engine.processes.process_spec import ProcessSpec
from aiida.engine.processes.states import Wait
from aiida.orm import Data, Dict, GraphNode, ProcessNode
from aiida.orm.nodes.data.base import to_aiida_type

__all__ = ('GraphProcess', 'TaskProcess', 'launched_as', 'task_node')


class TaskProcess(FunctionProcess):
    """A :class:`FunctionProcess` whose wrapped function takes and returns plain Python values.

    Input adaptation is inherited from ``Process``: Python annotations receive Python values and ``Data``
    annotations receive nodes. A returned value that is not already a ``Data`` node is stored with
    ``to_aiida_type``, so graph edges always carry provenance nodes.

    When the task declares its output ports, a returned tuple is mapped onto them in order.
    """

    NODE_INPUT_TYPES: t.ClassVar[bool] = False
    """Declare the Python types tasks consume, without legacy function annotation translation."""

    @override
    def _out_result(self, result: t.Any) -> None:
        outputs = self.spec().outputs
        annotation = get_annotations(self._func, eval_str=True).get('return')
        if isinstance(result, PortModel) or is_structured(annotation):
            if outputs.dynamic:
                msg = 'Task namespaces require a PortModel output declaration.'
                raise TypeError(msg)
            result = _stored(result, outputs)
        elif outputs.dynamic:
            result = _stored(result, None)
        else:
            declared = list(outputs)
            values = result if isinstance(result, tuple) else (result,)
            if len(values) != len(declared):
                msg = (
                    f'`{self.process_class.__name__}` declares {len(declared)} outputs {declared} but the function '
                    f'returned {len(values)} value(s).'
                )
                raise ValueError(msg)
            result = {name: _stored(value, outputs[name]) for name, value in zip(declared, values, strict=True)}
        super()._out_result(result)


def _stored(value: t.Any, port: t.Any) -> t.Any:
    """Return what is attached to one output port, which for a namespace is its fields stored one by one.

    A field of a structured type that is itself one names a namespace of output ports, exactly as it does among
    the inputs, so what a task produced for it is stored as the ports under it hold it rather than as one node
    holding the whole mapping.
    """
    if isinstance(port, PortNamespace):
        if port.dynamic:
            if not isinstance(value, Mapping):
                msg = f'Task output namespace `{port.name}` requires a mapping, got {type(value).__name__}.'
                raise TypeError(msg)
            stored = {}
            for name, item in value.items():
                port.validate_port_name(name)
                leaf = _stored(item, port.entry_port)
                if port.valid_type and not isinstance(leaf, port.valid_type):
                    msg = f'Invalid type {type(leaf)} for task output `{port.name}.{name}`: expected {port.valid_type}.'
                    raise TypeError(msg)
                stored[name] = leaf
            return stored

        fields = fields_of(type(value))
        if fields is None and isinstance(value, Mapping):
            return {name: _stored(item, port.get(name)) for name, item in value.items()}
        if fields is None:
            msg = f'Task output namespace `{port.name}` requires PortModel values, got {type(value).__name__}.'
            raise TypeError(msg)
        stored = {}
        for field in fields:
            item = getattr(value, field.name)
            if not field.required and item == field.default:
                continue
            stored[field.name] = _stored(item, port[field.name] if field.name in port else None)
        return stored

    return value if isinstance(value, Data) else to_aiida_type(value)


class GraphProcess(Process):
    """Run a graph of tasks, dispatching each as a child process.

    Every run that is ready is submitted, so it is a process in its own right: it gets its own node, its own entry
    in the provenance graph under the name the graph gave it, and it is scheduled like any other process. What to
    run next is decided by :class:`~aiida.engine.processes.graphs.run.GraphRun`, which knows of no engine, so this
    holds the ports, submits what it is told to, waits, and attaches what came out.
    """

    _node_class = GraphNode

    _GRAPH = 'graph'
    _GRAPH_INPUTS = 'graph_inputs'
    _GRAPH_BINDINGS = 'graph_bindings'

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
        spec.input_namespace(
            cls._GRAPH_BINDINGS,
            dynamic=True,
            required=False,
            non_db=True,
            help='Captured task values, checkpointed separately from the declaration.',
        )
        spec.outputs.dynamic = True
        spec.exit_code(400, 'ERROR_TASK_FAILED', message='The task `{task}` did not finish successfully.')

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self._run: GraphRun | None = None
        self._saved: dict[str, t.Any] = {}

    @override
    def _create_and_setup_db_record(self) -> t.Any:
        """Check raw graph inputs after engine parsing but before provenance is stored."""
        graph = GraphSpec.from_dict(self.inputs[self._GRAPH].get_dict())
        supplied = dict(self.inputs.get(self._GRAPH_INPUTS, {}))
        bindings = dict(self.inputs.get(self._GRAPH_BINDINGS, {}))
        stored = graph.serialize_inputs({**bindings, **supplied})
        validate_bound_tasks(graph, stored)
        public = {name: value for name, value in stored.items() if name not in bindings}
        captured = {name: stored[name] for name in bindings}
        self._input_sources = AttributesFrozendict(
            {**self._input_sources, self._GRAPH_INPUTS: public, self._GRAPH_BINDINGS: captured}
        )
        prepared = graph.input_spec().prepare(stored)
        self._parsed_inputs = AttributesFrozendict(
            {
                **self.inputs,
                self._GRAPH_INPUTS: {name: value for name, value in prepared.items() if name not in bindings},
                self._GRAPH_BINDINGS: {name: prepared[name] for name in bindings},
            }
        )
        return super()._create_and_setup_db_record()

    @classmethod
    def launch_inputs(
        cls,
        body: GraphSpec,
        inputs: dict[str, t.Any],
        *,
        bindings: dict[str, t.Any] | None = None,
    ) -> dict[str, t.Any]:
        """Return the inputs with which to launch a graph: the declaration, and the values to run it on.

        The two travel side by side, so one declaration serves every run. The values are serialized here because
        they arrive in a dynamic namespace, which declares no ports of its own to do it.

        :param body: the graph to run.
        :param inputs: the values for the inputs the graph declares.
        :param bindings: captured values for private prepared boundary inputs.
        """
        captured = bindings or {}
        stored = body.serialize_inputs({**captured, **inputs})
        validate_bound_tasks(body, stored)
        private = set()
        for name in captured:
            for task_name, path in body.inputs[name]:
                placed = body.task(task_name)
                if not isinstance(placed, ProcessTask):
                    continue
                port: t.Any = placed.spec.inputs
                for segment in path.split('.'):
                    if getattr(port, 'non_db', False) or getattr(port, 'is_metadata', False):
                        private.add(name)
                    if not isinstance(port, PortNamespace) or segment not in port:
                        break
                    port = port[segment]
                if getattr(port, 'non_db', False) or getattr(port, 'is_metadata', False):
                    private.add(name)
        launch = {
            cls._GRAPH: Dict(dict=body.to_dict()),
            cls._GRAPH_INPUTS: {name: value for name, value in stored.items() if name not in private},
        }
        if private:
            launch[cls._GRAPH_BINDINGS] = {name: stored[name] for name in private}
        return launch

    @property
    @override
    def output_ports(self) -> PortNamespace:
        """Use the stored graph declaration without mutating the shared process spec."""
        return self.graph.output_spec()

    @property
    def run_state(self) -> GraphRun:
        """Return how far the graph has got, read back from the declaration and what was checkpointed."""
        if self._run is None:
            graph = GraphSpec.from_dict(self.inputs[self._GRAPH].get_dict())
            self._run = GraphRun.from_dict(
                graph=graph,
                given=graph.serialize_inputs(
                    {
                        **dict(self._input_sources.get(self._GRAPH_BINDINGS, {})),
                        **dict(self._input_sources.get(self._GRAPH_INPUTS, {})),
                    }
                ),
                data=self._saved,
            )

        return self._run

    @override
    def save_instance_state(self, out_state: MutableMapping[str, t.Any], save_context: t.Any) -> None:
        super().save_instance_state(out_state, save_context)
        out_state['run'] = self.run_state.to_dict()
        out_state['graph_bindings'] = self._encode_input_args(dict(self._input_sources.get(self._GRAPH_BINDINGS, {})))
        out_state['graph_input_sources'] = self._encode_input_args(
            dict(self._input_sources.get(self._GRAPH_INPUTS, {}))
        )

    @override
    def load_instance_state(self, saved_state: MutableMapping[str, t.Any], load_context: t.Any) -> None:
        super().load_instance_state(saved_state, load_context)
        self._run = None
        self._saved = dict(saved_state.get('run', {}))
        if 'graph_bindings' in saved_state:
            self._input_sources = AttributesFrozendict(
                {
                    **self._input_sources,
                    self._GRAPH_BINDINGS: self._decode_input_args(saved_state['graph_bindings']),
                }
            )
        if 'graph_input_sources' in saved_state:
            self._input_sources = AttributesFrozendict(
                {
                    **self._input_sources,
                    self._GRAPH_INPUTS: self._decode_input_args(saved_state['graph_input_sources']),
                }
            )

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
        process_class, inputs = launched_as(start)
        metadata = {**inputs.get('metadata', {}), 'call_link_label': start.instance}
        node = self.submit(process_class, **{**inputs, 'metadata': metadata})
        assert node.pk is not None
        self.run_state.started(start.instance, node.pk)
        self.report(f'dispatched task `{start.instance}` as {node.pk}')

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

    @override
    def _build_process_label(self) -> str:
        """Return the name of the graph, so that a run of one is told apart from a run of another."""
        return self.graph.identifier or super()._build_process_label()


def launched_as(start: Start) -> tuple[type[Process], dict[str, t.Any]]:
    """Return the process that runs one start, and the inputs to run it with.

    A graph decides what to start as :class:`~aiida.engine.processes.graphs.run.Start` values, which say
    nothing about processes. This is what turns one of them into something :func:`~aiida.engine.launch.run`
    or :func:`~aiida.engine.launch.submit` takes, and it is what anything running a graph other than
    :class:`GraphProcess` needs, since the translation is the same wherever the decision came from.

    :param start: one run a graph asked for.
    :return: the process class to run, and the inputs to run it with.
    :raises ValueError: if the task is of a kind that has no way to run here, which a kind added to the
        declaration without one would be.
    """
    if start.body is not None:
        return GraphProcess, GraphProcess.launch_inputs(start.body, start.inputs)

    if isinstance(start.task, ProcessTask):
        process_class = start.task.spec.process_class

        if issubclass(process_class, TaskWorkChain):
            return process_class, launch_under_namespace(process_class, start.inputs)

        return process_class, start.inputs

    msg = f'`{start.task.name}` is of kind `{start.task.kind}`, which this version of AiiDA cannot run.'
    raise ValueError(msg)


def task_node() -> ProcessNode:
    """Return the node of the task that is running.

    A step that has to be safe to run twice records what it has already done on its own node, and reads it back
    before doing it again. The node is what makes that possible: the engine resumes a task against the same
    one, so what was written is still there, while running the task afresh gives a new node and so a clean
    slate. Anything a step would otherwise have to invent an identity for, a remote directory or a job id,
    belongs here.

    :raises RuntimeError: if no process is running, since there is then no node to record anything against.
    """
    # `current` is declared on the state machine, which knows nothing of nodes; what runs here is always
    # this package's `Process`, and that is what carries one.
    process = t.cast('Process | None', Process.current())

    if process is None:
        msg = 'no process is running, so there is no task node to record against.'
        raise RuntimeError(msg)

    return process.node
