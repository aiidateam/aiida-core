from __future__ import annotations

import traceback
from typing import Any

from node_graph.link import TaskLink

from aiida.engine.processes import Process
from aiida.engine.processes.exit_code import ExitCode
from aiida.workgraph.enums import TaskAction, TaskState
from aiida.workgraph.socket import TaskSocketNamespace
from aiida.workgraph.task import Task
from aiida.workgraph.utils import get_nested_dict

from .task_actions import TaskActionManager
from .task_state import TaskStateManager

MAX_NUMBER_AWAITABLES_MSG = 'The maximum number of subprocesses has been reached: {}. Cannot launch the job: {}.'

process_task_types = [
    'CALCJOB',
    'WORKCHAIN',
    'GRAPH',
    'SUBGRAPH',
    'PYTHONJOB',
    'SHELLJOB',
]


class TaskManager:
    """Manages task execution, state updates, and error handling."""

    def __init__(self, logger, runner, process: Process):
        """
        :param logger: A logger instance.
        :param runner: An AiiDA runner.
        :param process: The AiiDA process object that orchestrates the entire WorkGraph.
        """
        self.logger = logger
        self.runner = runner
        self.process = process
        # Sub-managers
        self.state_manager = TaskStateManager(logger, process)
        self.action_manager = TaskActionManager(self.state_manager, logger, process)

    @property
    def ctx(self):
        """Read the context off the process, which replaces it wholesale when loading from a checkpoint."""
        return self.process.ctx

    def get_task(self, name: str):
        """Get task from the context."""
        task = self.process.wg.tasks[name]
        task.set_input_resolver(self.get_socket_value)
        task.action = self.state_manager.get_task_runtime_info(name, 'action')
        # update task results
        # namespace socket does not have a value, but _value
        for socket in task.outputs:
            if socket._identifier == 'workgraph.namespace':
                socket._value = get_nested_dict(self.ctx._task_results[name], socket._name, default=None)
            else:
                socket.value = get_nested_dict(self.ctx._task_results[name], socket._name, default=None)
        return task

    def set_task_results(self) -> None:
        from node_graph.config import BUILTIN_TASKS

        for task in self.process.wg.tasks:
            if task.name in BUILTIN_TASKS:
                # skip built-in nodes, they are not executed
                continue
            if self.state_manager.get_task_runtime_info(task.name, 'action') == TaskAction.RESET:
                self.state_manager.reset_task(task.name)
            self.state_manager.update_task_state(task.name)

    def is_workgraph_finished(self) -> tuple[bool, ExitCode | None]:
        """Check if the workgraph is finished.
        For `while` workgraph, we need check its conditions"""
        is_finished = True
        failed_tasks = []
        not_finished_tasks = []
        for task in self.process.wg.tasks:
            # if the task is in mapped state, we need to check its children (mapped tasks)
            if self.state_manager.get_task_runtime_info(task.name, 'state') == TaskState.MAPPED:
                self.state_manager.update_template_task_state(task.name)
            elif self.state_manager.get_task_runtime_info(task.name, 'state') in {
                TaskState.RUNNING,
                TaskState.CREATED,
                TaskState.PLANNED,
                TaskState.READY,
            }:
                not_finished_tasks.append(task.name)
                is_finished = False
            elif self.state_manager.get_task_runtime_info(task.name, 'state') == TaskState.FAILED:
                failed_tasks.append(task.name)
        if is_finished and len(failed_tasks) > 0:
            message = f'WorkGraph finished, but tasks: {failed_tasks} failed. Thus all their child tasks are skipped.'
            self.process.report(message)
            result = ExitCode(302, message)
        else:
            result = None
        # print("not_finished_tasks: ", not_finished_tasks)
        return is_finished, result

    def continue_workgraph(self) -> None:
        """
        Resume the WorkGraph by looking for tasks that are ready to run.
        """
        # self.process.report("Continue workgraph.")
        task_to_run = []
        for task in self.process.wg.tasks:
            # update task state
            if (
                self.state_manager.get_task_runtime_info(task.name, 'state')
                in {
                    TaskState.CREATED,
                    TaskState.RUNNING,
                    TaskState.FINISHED,
                    TaskState.FAILED,
                    TaskState.SKIPPED,
                    TaskState.MAPPED,
                }
                or task.name in self.ctx._executed_tasks
            ):
                continue
            ready, _ = self.state_manager.is_task_ready_to_run(task.name)
            if ready:
                task_to_run.append(task.name)
        self.process.report('tasks ready to run: {}'.format(','.join(task_to_run)))
        self.run_tasks(task_to_run)

    def should_run_task(self, task: Task) -> bool:
        """Check if the task should run."""
        name = task.name
        # skip if the max number of awaitables is reached
        if task.task_type.upper() in process_task_types:
            if len(self.process._awaitables) >= self.process.wg.max_number_jobs:
                self.process.report(MAX_NUMBER_AWAITABLES_MSG.format(self.process.wg.max_number_jobs, name))
                return False
        # skip if the task is already executed or if the task is in a skippped state
        if (
            name in self.ctx._executed_tasks
            or self.state_manager.get_task_runtime_info(name, 'state') == TaskState.SKIPPED
        ):
            return False
        return True

    def run_tasks(self, names: list[str], continue_workgraph: bool = True) -> None:
        """Run tasks.
        Task type includes: Node, Data, CalcFunction, WorkFunction, CalcJob, WorkChain, GraphBuilder,
        WorkGraph, PythonJob, ShellJob, While, If, Zone, GetContext, SetContext, Normal.

        """
        for name in names:
            # skip if the max number of awaitables is reached
            task = self.process.wg.tasks[name]
            task.action = self.state_manager.get_task_runtime_info(name, 'action')
            if not self.should_run_task(task):
                continue

            self.ctx._executed_tasks.append(name)
            # print("-" * 60)

            self.logger.info(f'Run task: {name}, type: {task.task_type}')
            inputs = self.get_inputs(name)
            # print("kwargs: ", inputs["kwargs"])
            self.ctx._task_results[task.name] = {}
            task_type = task.task_type.upper()
            if task_type == 'PYFUNCTION':
                if task.spec.metadata.get('is_coroutine', False):
                    self.execute_process_task(task, **inputs)
                else:
                    self.execute_function_task(task, continue_workgraph, **inputs)
            elif task_type in ['CALCFUNCTION', 'WORKFUNCTION']:
                self.execute_function_task(task, continue_workgraph, **inputs)
            elif task_type in [
                'CALCJOB',
                'WORKCHAIN',
                'SHELLJOB',
                'PYTHONJOB',
                'SUBGRAPH',
                'GRAPH',
                'MONITOR',
            ]:
                self.execute_process_task(task, **inputs)
            elif task_type == 'WHILE':
                self.execute_while_task(task)
            elif task_type == 'IF':
                self.execute_if_task(task)
            elif task_type == 'ZONE':
                self.execute_zone_task(task)
            elif task_type == 'MAP':
                self.execute_map_task(task, inputs['kwargs'])
            elif task_type == 'NORMAL':
                self.execute_normal_task(
                    task,
                    continue_workgraph,
                    **inputs,
                )
            else:
                self.process.report(f'Unknown task type {task_type}')
                self.state_manager.set_task_runtime_info(name, 'state', TaskState.FAILED)

    def execute_function_task(self, task, continue_workgraph=None, args=None, kwargs=None, var_kwargs=None):
        """Execute a CalcFunction or WorkFunction task."""

        try:
            process, _ = task.execute(args, kwargs, var_kwargs)
            self.state_manager.set_task_runtime_info(task.name, 'process', process)
            self.state_manager.update_task_state(task.name)
        except Exception as e:
            error_traceback = traceback.format_exc()  # Capture the full traceback
            self.logger.error(f'Error in task {task.name}: {e}\n{error_traceback}')
            self.state_manager.update_task_state(task.name, success=False)
        # exclude the current tasks from the next run
        if continue_workgraph:
            self.continue_workgraph()

    def execute_process_task(self, task, args=None, kwargs=None, var_kwargs=None):
        """Execute a CalcJob or WorkChain task."""
        try:
            process, state = task.execute(
                engine_process=self.process,
                args=args,
                kwargs=kwargs,
                var_kwargs=var_kwargs,
            )
            self.state_manager.set_task_runtime_info(task.name, 'state', state)
            self.state_manager.set_task_runtime_info(task.name, 'action', '')
            self.state_manager.set_task_runtime_info(task.name, 'process', process)
            # update the parent task state of mappped tasks
            if self.process.wg.tasks[task.name].map_data:
                parent_task_name = self.process.wg.tasks[task.name].map_data['parent']
                if self.process.node.get_task_state(parent_task_name) == TaskState.PLANNED:
                    self.process.node.set_task_state(parent_task_name, state)
            self.process.to_context(**{task.name: process})
        except Exception as e:
            error_traceback = traceback.format_exc()  # Capture the full traceback
            self.logger.error(f'Error in task {task.name}: {e}\n{error_traceback}')  # Log the error with traceback
            self.state_manager.update_task_state(task.name, success=False)

    def execute_while_task(self, task):
        """Execute a WHILE task."""
        # TODO refactor this for while, if and zone
        # in case of an empty zone, it will finish immediately
        name = task.name
        if self.state_manager.are_childen_finished(name)[0]:
            self.state_manager.update_while_task_state(name)
        else:
            # check the conditions of the while task
            should_run = self.should_run_while_task(name)
            if not should_run:
                self.state_manager.set_task_runtime_info(name, 'state', TaskState.FINISHED)
                self.state_manager.set_tasks_state(
                    [child.name for child in self.process.wg.tasks[name].children],
                    TaskState.SKIPPED,
                )
                self.state_manager.update_parent_task_state(name)
                self.process.report(
                    f'While Task {name}: Condition not fullilled, task finished. Skip all its children.'
                )
            else:
                execution_count = self.state_manager.get_task_runtime_info(name, 'execution_count')
                self.state_manager.set_task_runtime_info(name, 'state', TaskState.RUNNING)
                self.state_manager.set_task_runtime_info(name, 'execution_count', execution_count + 1)
        self.continue_workgraph()

    def execute_if_task(self, task):
        # in case of an empty zone, it will finish immediately
        name = task.name
        if self.state_manager.are_childen_finished(name)[0]:
            self.state_manager.update_zone_task_state(name)
        else:
            should_run = self.should_run_if_task(name)
            if should_run:
                self.state_manager.set_task_runtime_info(name, 'state', TaskState.RUNNING)
            else:
                self.state_manager.set_tasks_state([child.name for child in task.children], TaskState.SKIPPED)
                self.state_manager.update_zone_task_state(name)
        self.continue_workgraph()

    def execute_zone_task(self, task):
        # in case of an empty zone, it will finish immediately
        name = task.name
        if self.state_manager.are_childen_finished(name)[0]:
            self.state_manager.update_zone_task_state(name)
        else:
            self.state_manager.set_task_runtime_info(name, 'state', TaskState.RUNNING)
        self.continue_workgraph()

    def execute_map_task(self, task, kwargs):
        """
        1. Clone the subgraph tasks for each item in `source`.
        2. Mark this MAP node as running and schedule a continuation.
        """
        name = task.name
        # we also store the links, so that we can load it in the GUI
        map_info = {'prefix': [], 'children': [], 'links': []}
        if self.state_manager.are_childen_finished(name)[0]:
            self.state_manager.update_zone_task_state(name)
        else:
            self.state_manager.set_task_runtime_info(name, 'state', TaskState.RUNNING)
            item_task = next(child for child in task.children if child.identifier == 'workgraph.map_item')
            source = kwargs['source']
            map_info['prefix'] = list(source.keys())
            for prefix, value in source.items():
                new_tasks, new_links = self.generate_mapped_tasks(task, prefix=prefix)
                self.update_map_item_task_state(item_task, prefix, value)
            map_info['children'] = list(new_tasks.keys())
            map_info['links'] = new_links
        self.state_manager.set_task_runtime_info(name, 'map_info', map_info)
        # gather task finishes immediately
        gather_task = task.gather_item_task
        self.state_manager.set_task_runtime_info(gather_task.name, 'state', TaskState.FINISHED)

        self.continue_workgraph()

    def execute_normal_task(self, task, continue_workgraph=None, args=None, kwargs=None, var_kwargs=None):
        """Execute a Normal task."""
        name = task.name

        # A "context" key is special and should be passed to the context manager
        # TODO this is hard coded for now, need to be refactored
        if 'context' in task.args_data['kwargs']:
            self.ctx.task_name = name
            kwargs.update({'context': self.ctx})
        for key in task.args_data['args']:
            kwargs.pop(key, None)
        try:
            results, _ = task.execute(args, kwargs, var_kwargs)
            self.state_manager.update_normal_task_state(name, results)
        except Exception as e:
            error_traceback = traceback.format_exc()
            self.logger.error(f'Error in task {task.name}: {e}\n{error_traceback}')
            self.state_manager.update_normal_task_state(name, results=None, success=False)
        if continue_workgraph:
            self.continue_workgraph()

    def get_socket_value(self, socket) -> Any:
        """Get the value of the socket recursively."""
        socket_value = None
        if isinstance(socket, TaskSocketNamespace):
            socket_value = {}
            for name, sub_socket in socket._sockets.items():
                value = self.get_socket_value(sub_socket)
                if value is None or (isinstance(value, dict) and value == {}):
                    continue
                socket_value[name] = value
        else:
            socket_value = socket.property.value
        if (
            socket._task is not None
            and socket._full_name.split('.')[0] == 'inputs'
            and socket._metadata.extras.get('value_source') == 'property'
        ):
            return socket_value
        links = socket._links
        if len(links) == 1:
            link = links[0]
            if self.ctx._task_results.get(link.from_task.name):
                # handle the special socket _wait, _outputs
                if link.from_socket._scoped_name == '_wait':
                    return socket_value
                elif link.from_socket._scoped_name == '_outputs':
                    socket_value = self.ctx._task_results[link.from_task.name]
                else:
                    socket_value = get_nested_dict(
                        self.ctx._task_results[link.from_task.name],
                        link.from_socket._scoped_name,
                        default=None,
                    )
        # handle the case of multiple outputs
        elif len(links) > 1:
            socket_value = {}
            for link in links:
                item_name = f'{link.from_task.name}_{link.from_socket._scoped_name}'
                # handle the special socket _wait, _outputs
                if link.from_socket._scoped_name in ['_wait', '_outputs']:
                    continue
                if self.ctx._task_results[link.from_task.name] is None:
                    socket_value[item_name] = None
                else:
                    socket_value[item_name] = self.ctx._task_results[link.from_task.name][link.from_socket._scoped_name]
        return socket_value

    def get_inputs(
        self, name: str
    ) -> tuple[
        list[Any],
        dict[str, Any],
        list[Any] | None,
        dict[str, Any] | None,
        dict[str, Any],
    ]:
        """Get input based on the links."""
        from aiida.workgraph.utils import update_nested_dict_with_special_keys

        args = []
        kwargs = {}
        var_kwargs = None
        task = self.process.wg.tasks[name]
        inputs = {}
        for prop in task.properties:
            inputs[prop.name] = prop.value

        inputs.update(self.get_socket_value(task.inputs))

        for name, input in inputs.items():
            # only need to check the top level key
            key = name.split('.')[0]
            if key in task.args_data['args']:
                args.append(input)
            elif key in task.args_data['kwargs']:
                kwargs[name] = input
            elif key == task.args_data['var_kwargs']:
                var_kwargs = input
        for i, key in enumerate(task.args_data['args']):
            kwargs[key] = args[i]
        # update the port namespace
        kwargs = update_nested_dict_with_special_keys(kwargs)
        return {
            'args': args,
            'kwargs': kwargs,
            'var_kwargs': var_kwargs,
        }

    def should_run_while_task(self, name: str) -> tuple[bool, Any]:
        """Check if the while task should run."""
        # check the conditions of the while task
        execution_count = self.state_manager.get_task_runtime_info(name, 'execution_count')
        not_excess_max_iterations = execution_count < self.process.wg.tasks[name].inputs.max_iterations.property.value
        conditions = [not_excess_max_iterations]
        inputs = self.get_inputs(name)
        kwargs = inputs['kwargs']
        if isinstance(kwargs['conditions'], list):
            for condition in kwargs['conditions']:
                value = get_nested_dict(self.ctx, condition)
                conditions.append(value)
        elif isinstance(kwargs['conditions'], dict):
            for _, value in kwargs['conditions'].items():
                conditions.append(value)
        else:
            conditions.append(kwargs['conditions'])
        return False not in conditions

    def should_run_if_task(self, name: str) -> tuple[bool, Any]:
        """Check if the IF task should run."""
        inputs = self.get_inputs(name)
        kwargs = inputs['kwargs']
        flag = kwargs['conditions']
        if kwargs['invert_condition']:
            return not flag
        return flag

    def get_all_children(self, name: str) -> list[str]:
        """Find all children of the zone_task, and their children recursively"""
        child_tasks = []
        task = self.process.wg.tasks[name]
        if not hasattr(task, 'children'):
            return child_tasks
        for child_task in task.children:
            child_tasks.append(child_task.name)
            child_tasks.extend(self.get_all_children(child_task.name))
        return child_tasks

    def generate_mapped_tasks(self, zone_task: Task, prefix: str) -> None:
        """
        Recursively clone the subgraph starting from zone_children,
        rewriting references to old tasks with new task names.
        """
        # keep track of the mapped tasks
        new_tasks = {}
        all_links = []
        child_tasks = self.get_all_children(zone_task.name)
        for child_task in child_tasks:
            # since the child task is mapped, it should be skipped
            self.state_manager.set_task_runtime_info(child_task, 'state', TaskState.MAPPED)
            task = self.copy_task(child_task, prefix)
            new_tasks[child_task] = task
            links = self.process.wg.tasks[child_task].inputs._all_links
            all_links.extend(links)
        # fix references in the newly mapped tasks (children, input_links, etc.)
        new_links = self._patch_cloned_tasks(new_tasks, all_links)
        # update process.wg.connectivity so the new tasks are recognized in child_node, zone references, etc.
        self._patch_connectivity(new_tasks)
        return new_tasks, new_links

    def update_map_item_task_state(self, item_task, prefix, value: Any):
        new_name = f'{prefix}_{item_task.name}'
        self.ctx._task_results[new_name]['key'] = prefix
        self.ctx._task_results[new_name]['value'] = value
        self.state_manager.set_task_runtime_info(new_name, 'state', TaskState.FINISHED)

    def copy_task(self, name: str, prefix: str) -> Task:
        import uuid

        # keep track of the mapped tasks
        if not self.process.wg.tasks[name].mapped_tasks:
            self.process.wg.tasks[name].mapped_tasks = {}
        task_data = self.process.wg.tasks[name].to_dict()
        new_name = f'{prefix}_{name}'
        task_data['name'] = new_name
        task_data['map_data'] = {'parent': name, 'prefix': prefix}
        task_data['uuid'] = str(uuid.uuid4())
        # Reset runtime states
        self.ctx._task_results[new_name] = {}
        self.state_manager.set_task_runtime_info(new_name, 'state', TaskState.PLANNED)
        self.state_manager.set_task_runtime_info(new_name, 'action', '')
        # Insert new_data in ctx._tasks
        task = self.process.wg.add_task_from_dict(task_data)
        self.process.wg.tasks[name].mapped_tasks[prefix] = task
        return task

    def _patch_cloned_tasks(
        self,
        new_tasks: dict[str, Task],
        all_links: list[TaskLink],
    ):
        """
        For each newly mapped task, fix references (children, input_links, etc.)
        from old_name -> new_name.
        """
        for orginal_name, task in new_tasks.items():
            orginal_task = self.process.wg.tasks[orginal_name]
            # fix children references
            if hasattr(orginal_task, 'children'):
                for child_task in orginal_task.children:
                    task.children.add(new_tasks[child_task.name])
            # since this is a newly created task, it should not have any mapped tasks
            task.mapped_tasks = None
            # fix parent reference
            if orginal_task.parent is not None:
                if orginal_task.parent.name in new_tasks:
                    task.parent = new_tasks[orginal_task.parent.name]
                else:
                    task.parent = orginal_task.parent
        # fix links references
        new_links = []
        for link in all_links:
            if link.to_task.name in new_tasks:
                to_node = new_tasks[link.to_task.name]
                to_socket = to_node.inputs[link.to_socket._scoped_name]
            else:
                # if the to_node is not in the new_tasks, skip
                continue
            new_links.append(link.to_dict())
            if link.from_task.name in new_tasks:
                from_node = new_tasks[link.from_task.name]
                from_socket = from_node.outputs[link.from_socket._scoped_name]
            else:
                from_socket = link.from_socket
            self.process.wg.add_link(
                from_socket,
                to_socket,
            )
        return new_links

    def _patch_connectivity(self, new_tasks: dict[str, Task]) -> None:
        """
        Update the global connectivity for newly created tasks.
        """
        for name, task in new_tasks.items():
            # child_node
            new_child_node = []
            for child_task in self.process.wg.connectivity['child_node'][name]:
                if child_task in new_tasks:
                    new_child_node.append(new_tasks[child_task].name)
                else:
                    new_child_node.append(child_task)
            self.process.wg.connectivity['child_node'][task.name] = new_child_node
            # input_tasks
            new_input_tasks = []
            for input_task in self.process.wg.connectivity['zone'][name]['input_tasks']:
                if input_task in new_tasks:
                    new_input_tasks.append(new_tasks[input_task].name)
                else:
                    new_input_tasks.append(input_task)
            self.process.wg.connectivity['zone'][task.name] = {'input_tasks': new_input_tasks}
