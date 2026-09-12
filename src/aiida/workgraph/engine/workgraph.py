"""AiiDA workflow components: WorkGraph."""

from __future__ import annotations

import collections.abc
import logging
import typing as t

from aiida.engine.processes import communications as process_comms
from aiida.engine.processes.persistence import auto_persist
from aiida.engine.processes.states import Continue, Wait
from aiida.engine.processes.workchains.outline import _PropagateReturn
import kiwipy

from aiida.common.extendeddicts import AttributeDict
from aiida.common.lang import override
from aiida.orm import Node
from aiida.workgraph.enums import TaskState
from aiida.workgraph.orm.workgraph import WorkGraphNode

from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.process import Process
from typing import final

from aiida.engine.processes.workchains.workchain import WorkChainSpec
from .context_manager import ContextManager
from .awaitable_manager import AwaitableManager
from .task_manager import TaskManager
from .error_handler_manager import ErrorHandlerManager
from aiida.engine.processes.workchains.awaitable import Awaitable
from aiida.node_graph.config import BUILTIN_TASKS

if t.TYPE_CHECKING:
    from aiida.engine.runners import Runner  # pylint: disable=unused-import

__all__ = 'WorkGraph'


class WorkGraphSpec(WorkChainSpec):
    WORKGRAPH_DATA_KEY = 'workgraph_data'


@auto_persist('_awaitables')
class WorkGraphEngine(Process):
    """The `WorkGraph` class is used to construct workflows in AiiDA."""

    # used to create a process node that represents what happened in this process.
    _node_class = WorkGraphNode
    _spec_class = WorkGraphSpec
    _CONTEXT = 'CONTEXT'
    #: Intent of a message that carries a WorkGraph task action rather than a plumpy process action.
    CUSTOM_INTENT = 'custom'

    def __init__(
        self,
        inputs: dict | None = None,
        logger: logging.Logger | None = None,
        runner: 'Runner' | None = None,
        enable_persistence: bool = True,
    ) -> None:
        """Construct a WorkGraph instance.

        :param inputs: work graph inputs
        :param logger: aiida logger
        :param runner: work graph runner
        :param enable_persistence: whether to persist this work graph

        """

        super().__init__(inputs, logger, runner, enable_persistence=enable_persistence)
        self._awaitables: list[Awaitable] = []
        self._context = AttributeDict()
        self.ctx_manager = ContextManager(self._context, process=self, logger=self.logger)
        self.awaitable_manager = AwaitableManager(self._awaitables, self.runner, self.logger, self, self.ctx_manager)
        self.task_manager = TaskManager(self.ctx_manager, self.logger, self.runner, self, self.awaitable_manager)
        self.error_handler_manager = ErrorHandlerManager(self, self.ctx_manager, self.logger)

    @classmethod
    def define(cls, spec: WorkGraphSpec) -> None:
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
        #
        spec.exit_code(201, 'UNKNOWN_MESSAGE_TYPE', message='The message type is unknown.')
        spec.exit_code(202, 'UNKNOWN_TASK_TYPE', message='The task type is unknown.')
        #
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

    def _setup_metadata(self, metadata: dict) -> None:  # type: ignore[override]
        """Store common metadata on the ProcessNode and forward the rest."""
        super()._setup_metadata(metadata)

    @property
    def ctx(self) -> AttributeDict:
        """Get the context."""
        return self._context

    @override
    def save_instance_state(self, out_state: t.Dict[str, t.Any], save_context: t.Any) -> None:
        """Save instance state.

        :param out_state: state to save in

        :param save_context:
        :type save_context: :class:`!plumpy.persistence.LoadSaveContext`

        """
        super().save_instance_state(out_state, save_context)
        # Save the context
        out_state[self._CONTEXT] = self.ctx

    @override
    def load_instance_state(self, saved_state: t.Dict[str, t.Any], load_context: t.Any) -> None:
        from aiida.orm.utils.log import create_logger_adapter
        from aiida.workgraph import WorkGraph

        super().load_instance_state(saved_state, load_context)
        # Load the context
        self._context = saved_state[self._CONTEXT]
        # Load the WorkGraph
        # if `_wgdata` does not exist, which means this is the first time the process is run
        if '_wgdata' in self.ctx:
            self.wg = WorkGraph.from_dict(self.ctx._wgdata)
        # TODO: avoid hardcoding the logger
        self.node._logger = logging.getLogger('aiida.orm.nodes.process.workflow.workchain.WorkChainNode')
        # First time the property is called after the node is stored, create the logger adapter
        self.node._logger_adapter = create_logger_adapter(self.node._logger, self.node)
        self.set_logger(self.node._logger_adapter)
        # TODO I don't know why we need to reinitialize the context, awaitables, and task_manager
        # Need to initialize the context, awaitables, and task_manager
        self.ctx_manager = ContextManager(self._context, process=self, logger=self.logger)
        self.awaitable_manager = AwaitableManager(self._awaitables, self.runner, self.logger, self, self.ctx_manager)
        self.task_manager = TaskManager(self.ctx_manager, self.logger, self.runner, self, self.awaitable_manager)
        self.error_handler_manager = ErrorHandlerManager(self, self.ctx_manager, self.logger)
        # "_awaitables" is auto persisted.
        if self._awaitables:
            # For other awaitables, because they exist in the db, we only need to re-register the callbacks
            self.ctx._awaitable_actions = []
            self.awaitable_manager.action_awaitables()

    @override
    def run(self) -> t.Any:
        self.setup()
        return self._do_step()

    def _do_step(self) -> t.Any:
        """Execute the next step in the workgraph and return the result.

        If any awaitables were created, the process will enter in the Wait state,
        otherwise it will go to Continue.
        """
        # we will not remove the awaitables here,
        # we resume the workgraph in the callback function even
        # there are some awaitables left
        # self._awaitables = []
        result: t.Any = None

        try:
            self.task_manager.continue_workgraph()
        except _PropagateReturn as exception:
            finished, result = True, exception.exit_code
        else:
            finished, result = self.task_manager.is_workgraph_finished()

        # If the workgraph is finished or the result is an ExitCode, we exit by returning
        if finished:
            if isinstance(result, ExitCode):
                return result
            else:
                return self.finalize()

        if self._awaitables:
            return Wait(self._do_step, 'Waiting before next step')

        return Continue(self._do_step)

    def _store_nodes(self, data: t.Any) -> None:
        """Recurse through a data structure and store any unstored nodes that are found along the way

        :param data: a data structure potentially containing unstored nodes
        """
        if isinstance(data, Node) and not data.is_stored:
            data.store()
        elif isinstance(data, collections.abc.Mapping):
            for _, value in data.items():
                self._store_nodes(value)
        elif isinstance(data, collections.abc.Sequence) and not isinstance(data, str):
            for value in data:
                self._store_nodes(value)

    @override
    @final
    def on_exiting(self) -> None:
        """Ensure that any unstored nodes in the context are stored, before the state is exited

        After the state is exited the next state will be entered and if persistence is enabled, a checkpoint will
        be saved. If the context contains unstored nodes, the serialization necessary for checkpointing will fail.
        """
        super().on_exiting()
        try:
            self._store_nodes(self.ctx)
        except Exception:  # pylint: disable=broad-except
            # An uncaught exception here will have bizarre and disastrous consequences
            self.logger.exception('exception in _store_nodes called in on_exiting')

    @final
    def on_wait(self, awaitables: t.Sequence[t.Awaitable]):
        """Entering the WAITING state."""
        super().on_wait(awaitables)
        if self._awaitables:
            self.awaitable_manager.action_awaitables()
            self.report('Process status: {}'.format(self.node.process_status))
        else:
            self.call_soon(self.resume)

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

    def setup(self) -> None:
        """Setup the variables in the context."""
        from aiida.workgraph import WorkGraph
        from aiida.workgraph.utils import restore_workgraph_data_from_raw_inputs

        # track if the awaitable callback is added to the runner
        self.ctx._awaitable_actions = []
        self.ctx._new_data = {}
        self.ctx._executed_tasks = []
        # read the workgraph data
        wgdata = restore_workgraph_data_from_raw_inputs(self.inputs)
        self.wg = WorkGraph.from_dict(wgdata)
        # store the workgraph data in the context, so that one can resume from checkpoint
        self.ctx._wgdata = wgdata
        # init task results
        self.ctx._task_results = {}
        # create a builtin `_context` task with its results as the context variables
        self.ctx._task_results = {
            'graph_ctx': self.wg.ctx._value,
            'graph_inputs': self.wg.inputs._value,
            'graph_outputs': self.wg.outputs._value,
        }
        self.task_manager.set_task_results()
        self.task_manager.state_manager.update_meta_tasks('graph_inputs')
        # set meta-tasks state
        for task_name in BUILTIN_TASKS:
            self.task_manager.state_manager.set_task_runtime_info(task_name, 'state', TaskState.FINISHED)

    def apply_action(self, msg: dict) -> None:
        if msg['catalog'] == 'task':
            self.task_manager.action_manager.apply_task_actions(msg)
        else:
            self.report(f'Unknow message type {msg}')

    @override
    def message_receive(self, _comm: kiwipy.Communicator, msg: process_comms.MessageType) -> t.Any:
        """Dispatch WorkGraph task actions; defer every plumpy intent to the base implementation.

        :param _comm: the communicator that sent the message
        :param msg: the message
        :return: the outcome of processing the message, sent back as the response to the sender
        """
        if msg[process_comms.INTENT_KEY] == self.CUSTOM_INTENT:
            return self._schedule_rpc(self.apply_action, msg=msg)
        return super().message_receive(_comm, msg)

    def finalize(self) -> t.Optional[ExitCode]:
        """Finalize the workgraph.
        Output the results of the workgraph and the new data.
        """
        from aiida.workgraph.utils import resolve_node_link_managers

        # in case we expose the ctx and inputs as outputs directly
        self.task_manager.state_manager.update_meta_tasks('graph_ctx')
        self.task_manager.state_manager.update_meta_tasks('graph_inputs')
        self.out_many(resolve_node_link_managers(self.ctx._task_results['graph_outputs']))
        # output the new data
        if self.ctx._new_data:
            self.out('new_data', self.ctx._new_data)
        self.report('Finalize workgraph.')
        for task in self.wg.tasks:
            if self.task_manager.state_manager.get_task_runtime_info(task.name, 'state') == TaskState.FAILED:
                return self.exit_codes.TASK_FAILED
