from __future__ import annotations

from typing import Any

from node_graph.socket import BaseSocket, TaskSocketNamespace
from typing_extensions import assert_never

from aiida.orm import Data, ProcessNode
from aiida.orm.utils.serialize import serialize
from aiida.workgraph.enums import TERMINAL_TASK_STATES, RuntimeInfoKey, TaskState
from aiida.workgraph.orm.utils import deserialize_safe


class TaskStateManager:
    """
    Handles all low-level operations on tasks' states, runtime info,
    and relationships (parent/child).
    """

    def __init__(self, logger, process):
        """
        :param logger: Logger instance.
        :param process: The current AiiDA process.
        """
        self.logger = logger
        self.process = process

    @property
    def ctx(self):
        """Read the context off the process, which replaces it wholesale when loading from a checkpoint."""
        return self.process.ctx

    def get_task_runtime_info(self, name: str, key: RuntimeInfoKey) -> Any:
        """Fetch a task runtime property (e.g. process, state, action)."""
        match key:
            case 'process':
                value = self.process.node.get_task_process(name)
                return deserialize_safe(value) if value else None
            case 'state':
                return self.process.node.get_task_state(name)
            case 'action':
                return self.process.node.get_task_action(name)
            case 'execution_count':
                return self.process.node.get_task_execution_count(name)
            case _:
                raise ValueError(f'Invalid key: {key}')

    def set_task_runtime_info(self, name: str, key: RuntimeInfoKey, value: Any) -> None:
        """Set a task runtime property (e.g. process, state, action).
        All the runtime info are store into the process node, which allow us
        access this info outside the engine
        """
        match key:
            case 'process':
                serialized = serialize(value)
                self.process.node.set_task_process(name, serialized)
            case 'state':
                self.process.node.set_task_state(name, value)
            case 'action':
                self.process.node.set_task_action(name, value)
            case 'execution_count':
                self.process.node.set_task_execution_count(name, value)
            case 'map_info':
                self.process.node.set_task_map_info(name, value)
            case _:
                assert_never(key)

    def set_tasks_state(self, tasks: list[str], value: str) -> None:
        """
        Set the state for a list of tasks (and their children) to `value`.
        Typically used for skip or reset tasks.
        """
        for name in tasks:
            self.set_task_runtime_info(name, 'state', value)
            if hasattr(self.process.wg.tasks[name], 'children'):
                self.set_tasks_state([task.name for task in self.process.wg.tasks[name].children], value)
            # TODO should we also reset the mapped tasks?

    def update_task_state(self, name: str, success=True) -> None:
        """Update task state when the task is finished."""
        from aiida.workgraph.utils import resolve_node_link_managers

        task = self.process.wg.tasks[name]
        self.ctx._task_results.setdefault(name, {})
        if success:
            node = self.get_task_runtime_info(name, 'process')
            if isinstance(node, ProcessNode):
                state = node.process_state.value.upper()
                if node.is_finished_ok:
                    self.set_task_runtime_info(task.name, 'state', state)

                    self.ctx._task_results[name] = resolve_node_link_managers(node.outputs)
                    self.set_task_runtime_info(task.name, 'state', TaskState.FINISHED)
                    self.update_meta_tasks(name)
                    self.process.report(f'Task: {name}, type: {task.task_type}, finished.')
                    self.apply_socket_spec_extras_to_aiida_node(name, node)
                # all other states are considered as failed
                else:
                    self.ctx._task_results[name] = resolve_node_link_managers(node.outputs)
                    self.on_task_failed(name)
            elif isinstance(node, Data):
                output_name = next(
                    output_name for output_name in task.outputs._get_keys() if output_name not in ['_wait', '_outputs']
                )
                self.ctx._task_results[name] = {output_name: node}
                self.set_task_runtime_info(task.name, 'state', TaskState.FINISHED)
                self.update_meta_tasks(name)
                self.process.report(f'Task: {name} finished.')
        else:
            self.on_task_failed(name)
        # After finishing, inform the parent
        self.update_parent_task_state(name)

    def update_normal_task_state(self, name, results, success=True):
        """Set the results of a normal task.
        A normal task is created by decorating a function with @task().
        """

        if success:
            task = self.process.wg.tasks[name]
            if isinstance(results, tuple):
                # there are two built-in outputs: _wait and _outputs
                if len(task.outputs) - 2 != len(results):
                    self.on_task_failed(name)
                    return self.process.exit_codes.OUTPUS_NOT_MATCH_RESULTS
                output_names = [
                    output._name for output in task.outputs if output._metadata.extra.get('builtin_socket') is not True
                ]
                for i, output_name in enumerate(output_names):
                    self.ctx._task_results[name][output_name] = results[i]
            elif isinstance(results, dict):
                self.ctx._task_results[name] = results
            else:
                output_names = [
                    output_name for output_name in task.outputs._get_keys() if output_name not in ['_wait', '_outputs']
                ]
                # some task does not have any output
                if len(output_names) == 1:
                    self.ctx._task_results[name][output_names[0]] = results
                    if isinstance(results, Data):
                        results.store()
                        self.set_task_runtime_info(task.name, 'process', results)
                elif len(output_names) > 1:
                    self.process.exit_codes.OUTPUS_NOT_MATCH_RESULTS
            self.update_meta_tasks(name)
            self.set_task_runtime_info(name, 'state', TaskState.FINISHED)
            self.process.report(f'Task: {name} finished.')
        else:
            self.on_task_failed(name)
        self.update_parent_task_state(name)

    def update_meta_tasks(self, name: str) -> None:
        """Export task results to the context based on context mapping."""
        from aiida.workgraph.utils import get_nested_dict, resolve_node_link_managers, update_nested_dict

        for link in self.process.wg.links:
            if link.from_task.name == name and link.to_task.name in [
                'graph_ctx',
                'graph_outputs',
            ]:
                key = link.to_socket._scoped_name
                result_key = link.from_socket._scoped_name
                # built-in "_outputs" means the whole task result
                if result_key == '_outputs':
                    result = self.ctx._task_results[name]
                else:
                    result = get_nested_dict(self.ctx._task_results[name], result_key, default=None)
                result = resolve_node_link_managers(result)
                update_nested_dict(self.ctx._task_results[link.to_task.name], key, result)

    def reset_task(
        self,
        name: str,
        reset_process: bool = True,
        recursive: bool = True,
        reset_execution_count: bool = True,
    ) -> None:
        """
        Reset the task's state to PLANNED, optionally clearing the process reference
        and recursing to children. If the task is a WHILE, reset its execution_count.
        """
        self.logger.debug(f'Resetting task {name}.')
        self.set_task_runtime_info(name, 'state', TaskState.PLANNED)
        if reset_process:
            self.set_task_runtime_info(name, 'process', None)
        self.remove_executed_task(name)

        task_type = self.process.wg.tasks[name].task_type.upper()
        if task_type == 'WHILE':
            if reset_execution_count:
                self.set_task_runtime_info(name, 'execution_count', 0)
            for child_task in self.process.wg.tasks[name].children:
                self.reset_task(child_task.name, reset_process=False, recursive=False)
        elif task_type in ['IF', 'ZONE']:
            for child_task in self.process.wg.tasks[name].children:
                self.reset_task(child_task.name, reset_process=False, recursive=False)

        if recursive:
            # reset its child tasks
            child_names = self.process.wg.connectivity['child_node'][name]
            for child_name in child_names:
                self.reset_task(child_name, recursive=False)

        self.logger.debug(f'Task {name} was reset.')

    def remove_executed_task(self, name: str) -> None:
        """
        Remove tasks from `ctx._executed_tasks` if they match this name (or name.*).
        """
        self.ctx._executed_tasks = [label for label in self.ctx._executed_tasks if label.split('.')[0] != name]

    def is_task_ready_to_run(self, name: str) -> tuple[bool, str | None]:
        """
        Check if the task is ready to run. We consider parent states, input tasks, etc.
        For tasks inside a ZONE or with a parent task, we require the parent
        to be in a running state, and the zone's input tasks finished or failed.
        """
        parent_task = self.process.wg.tasks[name].parent
        parent_states = [True, True]

        # If the task has a parent zone
        if parent_task:
            state = self.get_task_runtime_info(parent_task.name, 'state')
            if state != TaskState.RUNNING:
                parent_states[1] = False

        # Check input tasks from the zone connectivity
        for child_task_name in self.process.wg.connectivity['zone'][name]['input_tasks']:
            child_state = self.get_task_runtime_info(child_task_name, 'state')
            if child_state not in TERMINAL_TASK_STATES:
                parent_states[0] = False
                break
        return all(parent_states), parent_states

    def on_task_failed(self, name: str) -> None:
        """
        Mark a task as FAILED, skip its children, and run any error handlers.
        """
        task_type = self.process.wg.tasks[name].task_type
        self.set_task_runtime_info(name, 'state', TaskState.FAILED)
        self.set_tasks_state(self.process.wg.connectivity['child_node'][name], TaskState.SKIPPED)
        msg = f'Task, {name}, type: {task_type}, failed.'
        process = self.get_task_runtime_info(name, 'process')
        if isinstance(process, ProcessNode):
            msg += f' Error message: {process.exit_message}'
        self.process.report(msg)
        self.process.error_handler_manager.run_error_handlers(name)

    def update_parent_task_state(self, name: str) -> None:
        """
        If a task has a parent (WHILE, IF, ZONE, MAP), notify the parent to update
        its own state. Also handle mapped tasks referencing a 'map_data.parent' node.
        """
        parent_task = self.process.wg.tasks[name].parent
        if parent_task:
            task_type = parent_task.task_type.upper()
            if task_type == 'WHILE':
                self.update_while_task_state(parent_task.name)
            elif task_type in ['IF', 'ZONE']:
                self.update_zone_task_state(parent_task.name)
            elif task_type == 'MAP':
                self.update_map_task_state(parent_task.name)

        # If the task is a mapped child, update its parent's "template" (the original map node)
        if self.process.wg.tasks[name].map_data:
            map_parent = self.process.wg.tasks[name].map_data['parent']
            self.update_template_task_state(map_parent)

    def update_while_task_state(self, name: str) -> None:
        """
        Called when a child of a WHILE task finishes. If all children are done, we decide
        whether to reset for the next iteration or finalize the WHILE.
        """
        finished, _ = self.are_childen_finished(name)

        if finished:
            self.process.report(f'While Task {name}: this iteration finished. Try to reset for the next iteration.')
            # reset the condition tasks
            for link in self.process.wg.tasks[name].inputs.conditions._links:
                self.reset_task(link.from_task.name, recursive=False)
            # reset the task and all its children, so that the task can run again
            # do not reset the execution count
            self.reset_task(name, reset_execution_count=False)

    def update_zone_task_state(self, name: str) -> None:
        """
        Update the state of an IF or ZONE block. Mark it FINISHED if children are done.
        """
        finished, _ = self.are_childen_finished(name)
        if finished:
            self.set_task_runtime_info(name, 'state', TaskState.FINISHED)
            self.process.report(f'Task: {name} finished.')
            self.update_parent_task_state(name)

    def update_map_task_state(self, name: str) -> None:
        """Update the map task state.
        1) check if all child tasks are finished.
        2) gather the results of all the mapped tasks.
        3) update the parent task state.
        """
        finished, _ = self.are_childen_finished(name)
        if finished:
            map_zone = self.process.wg.tasks[name]
            # gather the results of all the mapped tasks
            gather_task = map_zone.gather_item_task
            for input in gather_task.inputs:
                if input._name.startswith('_'):
                    continue
                results = {}
                link = input._links[0]
                for prefix, mapped_task in self.process.wg.tasks[gather_task.name].mapped_tasks.items():
                    results[prefix] = self.ctx._task_results[mapped_task.name][link.to_socket._name]
                self.ctx._task_results[name][link.to_socket._name] = results
            self.set_task_runtime_info(name, 'state', TaskState.FINISHED)
            # self.update_meta_tasks(name)
            self.process.report(f'Task: {name} finished.')
            self.update_meta_tasks(name)
            self.update_parent_task_state(name)

    def update_template_task_state(self, name: str) -> None:
        """Update the template task state.
        1) check if all child tasks are finished.
        2) gather the results of all the mapped tasks.
        3) update the parent task state.
        """
        finished, _ = self.are_childen_finished(name)
        if finished:
            # # gather the results of all the mapped tasks
            # results = {}
            # for prefix, mapped_task in self.process.wg.tasks[name].mapped_tasks.items():
            #     for output in mapped_task.outputs:
            #         if output._name in self.ctx._task_results[mapped_task.name]:
            #             results.setdefault(output._name, {})
            #             results[output._name][prefix] = self.ctx._task_results[mapped_task.name][output._name]
            # self.ctx._task_results[name] = results
            self.set_task_runtime_info(name, 'state', TaskState.FINISHED)
            # self.update_meta_tasks(name)
            self.process.report(f'Task: {name} finished.')
            self.update_parent_task_state(name)

    def are_childen_finished(self, name: str) -> tuple[bool, Any]:
        """Check if the child tasks are finished."""
        task = self.process.wg.tasks[name]
        finished = True
        if hasattr(task, 'children'):
            for child in task.children:
                if self.get_task_runtime_info(child.name, 'state') not in TERMINAL_TASK_STATES:
                    finished = False
                    break
        # check the mapped tasks
        mapped_tasks = task.mapped_tasks or {}
        for mapped_task in mapped_tasks.values():
            if self.get_task_runtime_info(mapped_task.name, 'state') not in TERMINAL_TASK_STATES:
                finished = False
                break
        return finished, None

    def apply_socket_spec_extras_to_aiida_node(self, name: str, node: ProcessNode) -> None:
        """Apply the socket spec extras to the AiiDA process node for a task."""
        task = self.process.wg.tasks[name]
        task.set_outputs_from_process_node(node)
        self.set_socket_spec_extra(task.outputs)

    @classmethod
    def set_socket_spec_extra(cls, socket: BaseSocket) -> None:
        """Set the socket spec extra to the AiiDA process node for a task."""
        if isinstance(socket, TaskSocketNamespace):
            for sub_socket in socket._sockets.values():
                cls.set_socket_spec_extra(sub_socket)
        elif isinstance(socket.value, Data):
            extras = {
                key: value
                for key, value in socket._metadata.extras.items()
                if key not in ['identifier', 'builtin_socket', 'function_socket']
            }
            socket.value.base.extras.set_many(extras)
