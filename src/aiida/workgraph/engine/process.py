"""The AiiDA process that executes a work graph."""

from __future__ import annotations

import logging
import typing as t

import kiwipy
from plumpy import process_comms
from plumpy.workchains import Stepper

from aiida.common.lang import override
from aiida.engine.processes.process_spec import ProcessSpec
from aiida.engine.processes.workchains.awaitable import Awaitable
from aiida.engine.processes.workchains.workflow_process import WorkflowProcess
from aiida.orm import WorkGraphNode
from aiida.workgraph.engine.error_handler_manager import ErrorHandlerManager
from aiida.workgraph.engine.stepper import DagStepper
from aiida.workgraph.engine.task_manager import TaskManager
from aiida.workgraph.enums import TaskActionMessage

if t.TYPE_CHECKING:
    from aiida.engine.runners import Runner
    from aiida.workgraph import WorkGraph

__all__ = ('WorkGraphProcess', 'WorkGraphSpec')


class WorkGraphSpec(ProcessSpec):
    WORKGRAPH_DATA_KEY = 'workgraph_data'


class WorkGraphProcess(WorkflowProcess):
    """Execute a work graph, scheduling its tasks by their data dependencies.

    A work chain declares its execution order up front as an outline; a work graph derives it from the links
    between tasks, which are only known once the graph is built. Everything else a work chain provides (context,
    awaitables, checkpointing, node lifecycle) applies unchanged, so this supplies a :class:`DagStepper` through the
    stepper hooks and inherits the rest.

    The one way it departs from :class:`~aiida.engine.processes.workchains.workchain.WorkChain` is concurrency: a
    work chain waits for everything a step launched before starting the next, whereas here independent branches
    stay in flight together. That is not overridden here; it follows from :class:`DagStepper` declaring
    ``awaitable_barrier = False``, which the work chain honours. Only two small work-graph-specific hooks remain,
    :meth:`_action_awaitables` (surface the waiting status in the report) and :meth:`_on_awaitable_resolved`
    (record the finished child's outcome on its task).
    """

    # Narrowing the node and spec classes is how every AiiDA process specialises its base; mypy sees plain mutable
    # class attributes and flags the covariance.
    _node_class = WorkGraphNode  # type: ignore[mutable-override]
    _spec_class = WorkGraphSpec  # type: ignore[mutable-override]

    def __init__(
        self,
        inputs: dict[str, t.Any] | None = None,
        logger: logging.Logger | None = None,
        runner: Runner | None = None,
        enable_persistence: bool = True,
    ) -> None:
        super().__init__(inputs, logger, runner, enable_persistence=enable_persistence)
        self._init_runtime_state()
        self._init_managers()

    def _init_runtime_state(self) -> None:
        """Initialise the state that is rebuilt on every load rather than restored from the checkpoint."""
        self._wg: WorkGraph | None = None

    def _init_managers(self) -> None:
        self.task_manager = TaskManager(self.logger, self.runner, self)
        self.error_handler_manager = ErrorHandlerManager(self, self.logger)

    @classmethod
    def define(cls, spec: WorkGraphSpec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input_namespace(
            'graph_inputs',
            dynamic=True,
            required=False,
            help='Graph level inputs',
        )
        spec.input_namespace(
            'tasks',
            dynamic=True,
            required=False,
            help='Tasks inputs',
        )
        spec.input_namespace(
            spec.WORKGRAPH_DATA_KEY,
            dynamic=True,
            required=False,
            help='WorkGraph data',
        )
        spec.exit_code(2, 'ERROR_SUBPROCESS', message='A subprocess has failed.')
        spec.outputs.dynamic = True
        spec.exit_code(201, 'UNKNOWN_MESSAGE_TYPE', message='The message type is unknown.')
        spec.exit_code(202, 'UNKNOWN_TASK_TYPE', message='The task type is unknown.')
        spec.exit_code(
            301,
            'OUTPUS_NOT_MATCH_RESULTS',
            message='The outputs of the process do not match the results.',
        )
        spec.exit_code(
            302,
            'TASK_FAILED',
            message='Some of the tasks failed.',
        )
        spec.exit_code(
            303,
            'TASK_NON_ZERO_EXIT_STATUS',
            message='Some of the tasks exited with non-zero status.',
        )

    @property
    def wg(self) -> WorkGraph:
        """The work graph being executed, rebuilt from the context the first time it is needed after a reload."""
        if self._wg is None:
            from aiida.workgraph import WorkGraph

            self._wg = WorkGraph.from_dict(self.ctx._wgdata)
        return self._wg

    def set_workgraph_data(self, wgdata: dict[str, t.Any]) -> None:
        """Install the graph data, keeping the live graph and the checkpointed copy in step."""
        from aiida.workgraph import WorkGraph

        self.ctx._wgdata = wgdata
        self._wg = WorkGraph.from_dict(wgdata)

    def _create_stepper(self) -> Stepper:
        stepper = DagStepper(self)  # type: ignore[arg-type]
        stepper.setup()
        return stepper

    def _recreate_stepper(self, saved_state: t.Any) -> Stepper:
        """Restore the stepper after a checkpoint.

        ``saved_state`` is unused: :class:`DagStepper` holds no state of its own, everything it needs lives in the
        context, which the base class has already restored. Notably :meth:`DagStepper.setup` must not run again,
        as it would reset the execution bookkeeping and rerun the finished tasks.
        """
        return DagStepper(self)  # type: ignore[arg-type]

    @override
    def load_instance_state(self, saved_state: t.MutableMapping[str, t.Any], load_context: t.Any) -> None:
        from aiida.orm.utils.log import create_logger_adapter

        # `WorkflowProcess.load_instance_state` re-registers the awaitable callbacks before returning, so the runtime
        # state it consults has to be in place first.
        self._init_runtime_state()

        # `no-untyped-call` here and below: both are unannotated aiida-core internals.
        super().load_instance_state(saved_state, load_context)  # type: ignore[no-untyped-call]

        # TODO: avoid hardcoding the logger
        self.node._logger = logging.getLogger('aiida.orm.nodes.process.workflow.workchain.WorkChainNode')  # type: ignore[assignment]
        # First time the property is called after the node is stored, create the logger adapter
        self.node._logger_adapter = create_logger_adapter(self.node._logger, self.node)  # type: ignore[no-untyped-call]
        self.set_logger(self.node._logger_adapter)

        self._init_managers()

    def _action_awaitables(self) -> None:
        """Register the awaitable callbacks (via `WorkflowProcess`), then surface the waiting status in the report log.

        `WorkflowProcess` records "Waiting for child processes: ..." only as the process status; echoing it to the
        report makes it visible in `verdi process report` when a graph pauses for its children.
        """
        super()._action_awaitables()
        if self._awaitables:
            self.report(f'Process status: {self.status}')

    def _on_awaitable_resolved(self, awaitable: Awaitable) -> None:
        """Record a finished child's outcome on its task before the process decides whether to resume.

        This is the only work-graph-specific step in the awaitable lifecycle. The rest, including resuming as soon
        as any child finishes rather than only once all do, comes from `WorkflowProcess`, because :class:`DagStepper`
        declares ``awaitable_barrier = False``.

        :param awaitable: the awaitable whose target process has terminated
        """
        self.task_manager.state_manager.update_task_state(awaitable.key)

    def _build_process_label(self) -> str:
        """Use the workgraph name as the process label."""
        return f'WorkGraph<{self.inputs[WorkGraphSpec.WORKGRAPH_DATA_KEY]["name"]}>'

    def on_create(self) -> None:
        """Called when a Process is created."""
        from aiida.workgraph.utils import save_workgraph_data

        super().on_create()
        raw_inputs = dict(self.inputs)
        self.node.label = raw_inputs[WorkGraphSpec.WORKGRAPH_DATA_KEY]['name']
        save_workgraph_data(self.node, raw_inputs)

    def apply_action(self, msg: TaskActionMessage) -> None:
        if msg['catalog'] == 'task':
            self.task_manager.action_manager.apply_task_actions(msg)
        else:
            self.report(f'Unknow message type {msg}')

    def message_receive(self, _comm: kiwipy.Communicator, msg: dict[str, t.Any]) -> t.Any:
        """Handle the work-graph-specific ``custom`` intent and defer every standard intent to the base class.

        Only the ``custom`` intent, which carries task actions such as pausing or skipping an individual task, is
        particular to a work graph. The rest belong to plumpy's message protocol, which decides such things as
        which key holds the pause text and whether a kill is forced; that protocol changes, so reimplementing it
        here means silently drifting out of step with it.

        :param _comm: the communicator that sent the message
        :param msg: the message
        :return: the outcome of processing the message, sent back as the response to the sender
        """
        if msg[process_comms.INTENT_KEY] == 'custom':
            return self._schedule_rpc(self.apply_action, msg=msg)

        return super().message_receive(_comm, msg)
