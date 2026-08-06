"""Data-dependency stepping for a work graph."""

from __future__ import annotations

import typing as t

from node_graph.config import BUILTIN_TASKS
from plumpy.workchains import Stepper

from aiida.engine.processes.exit_code import ExitCode
from aiida.workgraph.enums import TaskState

if t.TYPE_CHECKING:
    from aiida.workgraph.engine.process import WorkGraphProcess


class DagStepper(Stepper):
    """Drive a process by the data dependencies between its tasks instead of a declared outline.

    A :class:`~aiida.engine.processes.workchains.workchain.WorkChain` outline fixes at class-definition time both
    which steps exist and in what order they run. Here neither is known until the graph is built: a step means
    "launch whatever became ready since the last one", and readiness is derived from the links between tasks. Two
    consequences follow, and they are why this cannot be expressed as an outline:

    * A step may launch several tasks at once, and independent branches stay in flight together. The outline
      stepper's implicit barrier, waiting for everything launched in a step before starting the next, would
      serialise them.
    * The number of steps is a property of the graph, not of the class.

    The stepper deliberately keeps no state of its own. Everything it needs (the graph data, task results and
    execution bookkeeping) lives in the process context, which is checkpointed with the process, so restoring from
    a checkpoint is a matter of constructing a fresh instance against the restored context.
    """

    # Opt out of the outline barrier: awaitables persist across steps and the process resumes as each child
    # finishes, so a task whose inputs are ready starts while an unrelated task is still running.
    awaitable_barrier = False

    @property
    def process(self) -> WorkGraphProcess:
        """The process being stepped (:class:`~plumpy.workchains.Stepper` names it ``_workchain``)."""
        return t.cast('WorkGraphProcess', self._workchain)

    def setup(self) -> None:
        """Materialise the graph from the process inputs and seed the execution bookkeeping in the context.

        Called once, when the process starts. Restoring from a checkpoint must *not* call this: the context it
        writes is part of the checkpoint, so re-running it would discard the progress made so far.
        """
        from aiida.workgraph.utils import restore_workgraph_data_from_raw_inputs

        process = self.process
        # Track which awaitables already have a completion callback registered, see
        # `WorkGraphProcess._action_awaitables`.
        process.ctx._awaitable_actions = []
        process.ctx._new_data = {}
        process.ctx._executed_tasks = []

        wgdata = restore_workgraph_data_from_raw_inputs(dict(process.inputs or {}))
        process.set_workgraph_data(wgdata)

        # Expose the graph-level containers as if they were the results of tasks, so that links pointing at them
        # resolve through the same lookup as links between real tasks.
        process.ctx._task_results = {
            'graph_ctx': process.wg.ctx._value,
            'graph_inputs': process.wg.inputs._value,
            'graph_outputs': process.wg.outputs._value,
        }
        process.task_manager.set_task_results()
        process.task_manager.state_manager.update_meta_tasks('graph_inputs')
        for task_name in BUILTIN_TASKS:
            process.task_manager.state_manager.set_task_runtime_info(task_name, 'state', TaskState.FINISHED)

    def step(self) -> tuple[bool, t.Any]:
        """Launch every task whose inputs are now available, and report whether the graph is complete.

        :return: ``(finished, result)``. While tasks remain, ``(False, None)``. Once the graph is complete,
            ``result`` is the exit code reporting which tasks failed if any did, and otherwise whatever
            :meth:`finalize` returns after mapping the outputs.
        """
        process = self.process
        process.task_manager.continue_workgraph()
        finished, failure = process.task_manager.is_workgraph_finished()

        if not finished:
            return False, None

        # A graph that finished with failed tasks reports them through ``failure``, naming the tasks; the
        # outputs are not mapped in that case, since the graph did not produce them.
        if isinstance(failure, ExitCode):
            return True, failure

        return True, self.finalize()

    def finalize(self) -> ExitCode | None:
        """Map the graph outputs onto the process outputs once every task has reached a terminal state.

        :return: the ``TASK_FAILED`` exit code if any task failed, otherwise ``None``.
        """
        from aiida.workgraph.utils import resolve_node_link_managers

        process = self.process
        # Refresh the meta-tasks so that a graph exposing its context or inputs directly as outputs sees the
        # final values rather than those captured at setup.
        process.task_manager.state_manager.update_meta_tasks('graph_ctx')
        process.task_manager.state_manager.update_meta_tasks('graph_inputs')
        process.out_many(resolve_node_link_managers(process.ctx._task_results['graph_outputs']))

        if process.ctx._new_data:
            process.out('new_data', process.ctx._new_data)

        process.report('Finalize workgraph.')

        for task in process.wg.tasks:
            if process.task_manager.state_manager.get_task_runtime_info(task.name, 'state') == TaskState.FAILED:
                return t.cast(ExitCode, process.exit_codes.TASK_FAILED)

        return None

    def __str__(self) -> str:
        """Report progress, which ends up in ``verdi process status`` via ``WorkChain.on_run``."""
        return f'{len(self.process.ctx._executed_tasks)}/{len(self.process.wg.tasks)} tasks launched'
