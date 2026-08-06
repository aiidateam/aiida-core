from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from node_graph.task import Task as GraphTask
from node_graph.task import TaskSet
from node_graph.task_spec import BaseHandle, TaskSpec

import aiida
from aiida.workgraph.enums import TaskState
from aiida.workgraph.socket_spec import SocketSpecAPI

from .registry import RegistryHub, registry_hub

if TYPE_CHECKING:
    pass


class Task(GraphTask):
    """Represent a Task in the AiiDA WorkGraph.

    The class extends from node_graph.task.Task and add new
    attributes to it.
    """

    _REGISTRY: RegistryHub | None = registry_hub
    _SOCKET_SPEC_API = SocketSpecAPI

    _default_spec = TaskSpec(
        identifier='workgraph.task',
        task_type='Normal',
        inputs=_SOCKET_SPEC_API.namespace(),
        outputs=_SOCKET_SPEC_API.namespace(),
        catalog='Base',
        base_class_path='aiida.workgraph.task.Task',
    )

    def __init__(
        self,
        process: aiida.orm.ProcessNode | None = None,
        pk: int | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a Task instance.
        """
        super().__init__(
            **kwargs,
        )
        self.waiting_on = WaitingTaskSet(parent=self)
        self.process = process
        self.pk = pk
        self.state = TaskState.PLANNED
        self.action = ''
        self.show_socket_depth = 0
        self.parent = None
        self.map_data = None
        self.mapped_tasks = None
        self.execution_count = 0

    def to_dict(self, include_sockets: bool = False, should_serialize: bool = False) -> dict[str, Any]:
        from aiida.orm.utils.serialize import serialize

        tdata = super().to_dict(include_sockets=include_sockets, should_serialize=should_serialize)
        tdata['wait'] = [task.name for task in self.waiting_on]
        tdata['children'] = []
        tdata['execution_count'] = self.execution_count
        tdata['parent_task'] = [self.parent.name] if self.parent else [None]
        tdata['process'] = serialize(self.process) if self.process else serialize(None)
        tdata['metadata']['pk'] = self.process.pk if self.process else None

        return tdata

    def set_from_builder(self, builder: Any) -> None:
        """Set the task inputs from a AiiDA ProcessBuilder."""
        from aiida.workgraph.utils import get_dict_from_builder

        data = get_dict_from_builder(builder)
        self.set_inputs(data)

    @classmethod
    def new(cls, identifier: str | Callable, name: str | None = None) -> Task:
        """Create a task from a identifier."""
        from aiida.workgraph.tasks import TaskPool

        return super().new(identifier, name=name, TaskPool=TaskPool)

    @classmethod
    def from_dict(cls, data: dict[str, Any], TaskPool: Any | None = None) -> Task:
        """Create a task from a dictionary. This method initializes a Task instance with properties and settings
        defined within the provided data dictionary. If TaskPool is not specified, the default TaskPool from
        aiida.workgraph.tasks is used.

        Args:
            data (Dict[str, Any]): A dictionary containing the task's configuration.
            TaskPool (Optional[Any]): A pool of task configurations, defaults to None
            which will use the global TaskPool.

        Returns:
            Task: An instance of Task initialized with the provided data."""
        from aiida.workgraph.tasks import TaskPool as workgraph_TaskPool

        if TaskPool is None:
            TaskPool = workgraph_TaskPool
        task = GraphTask.from_dict(data, TaskPool=TaskPool)

        return task

    def update_from_dict(self, data: dict[str, Any]) -> None:
        from aiida.workgraph.orm.utils import deserialize_safe

        super().update_from_dict(data)
        process = data.get('process', None)
        if process and isinstance(process, str):
            process = deserialize_safe(process)
        self.process = process
        self.waiting_on.add(data.get('wait', []))
        self.map_data = data.get('map_data', None)

    def reset(self) -> None:
        self.process = None
        self.state = TaskState.PLANNED

    def update_state(self, data: dict[str, Any]) -> None:
        """Set the outputs of the task from a dictionary."""
        self.state = data['state']
        self.ctime = data['ctime']
        self.mtime = data['mtime']
        self.pk = data['pk']
        if data['pk'] is not None:
            node = aiida.orm.load_node(data['pk'])
            self.process = self.node = node
            if isinstance(node, aiida.orm.ProcessNode):
                self.set_outputs_from_process_node(node)
            elif isinstance(node, aiida.orm.Data):
                self.set_outputs_from_data_node(node)

    def set_outputs_from_process_node(self, node: aiida.orm.ProcessNode) -> None:
        from aiida.workgraph.utils import resolve_node_link_managers

        # if the process is finished ok, update the output sockets
        # note the task.state may not be the same as the node.process_state
        # for example, task.state can be `SKIPPED` if it is inside a conditional block,
        # even if the node.is_finished_ok is True
        self.process = node
        if node.is_finished_ok:
            self.outputs._set_socket_value(resolve_node_link_managers(node.outputs))

    def set_outputs_from_data_node(self, node: aiida.orm.Data) -> None:
        self.outputs[0].value = node

    def execute(self, args=None, kwargs=None, var_kwargs=None):
        """Execute the task."""
        from node_graph.task_spec import BaseHandle

        executor = self.get_executor().callable
        # the imported executor could be a wrapped function
        if isinstance(executor, BaseHandle) and hasattr(executor, '_callable'):
            executor = getattr(executor, '_callable')
        if var_kwargs is None:
            result = executor(*args, **kwargs)
        else:
            result = executor(*args, **kwargs, **var_kwargs)
        return result, TaskState.FINISHED

    def to_widget_value(self):
        from aiida.workgraph.utils import workgraph_to_short_json

        tdata = self.to_dict(include_sockets=True)
        wgdata = {'name': self.name, 'tasks': {self.name: tdata}, 'links': []}
        wgdata = workgraph_to_short_json(wgdata)
        return wgdata


class WaitingTaskSet(TaskSet):
    def add(self, tasks: list[str | Task] | str | Task) -> None:
        """Add tasks to the collection. Tasks can be a list or a single Task or task name."""
        normalize_tasks = super().add(tasks)
        for task in normalize_tasks:
            source = task.outputs._wait
            target = self.parent.inputs._wait
            self.graph.add_link(source, target)


class TaskHandle(BaseHandle):
    def __init__(self, spec):
        from aiida.workgraph import WorkGraph
        from aiida.workgraph.manager import get_current_graph

        super().__init__(spec, get_current_graph, graph_class=WorkGraph)

    def __call__(self, *args, **kwargs):
        """Build a task into the current graph; forbid calling a task from inside
        another running @task/@task.calcfunction/@task.workfunction body (i.e., during process execution)."""

        from aiida.engine import FunctionProcess, Process

        try:
            current = Process.current()
        except Exception:
            current = None

        # Forbid the nested call only when the current process runs a user Python
        # function in this interpreter: core's @calcfunction/@workfunction
        # (FunctionProcess), or any plugin process that opts in via the
        # `_runs_python_function_locally` marker (e.g. aiida-pythonjob's PyFunction).
        # Keying on the marker rather than importing the plugin keeps this module
        # free of any downstream dependency, a prerequisite for it living in core.
        if current is not None and (
            isinstance(current, FunctionProcess) or getattr(current, '_runs_python_function_locally', False)
        ):
            running = getattr(current, 'process_label', current.__class__.__name__)
            raise RuntimeError(
                'Invalid nested task call.\n\n'
                f"• You invoked task '{self.identifier}' from inside the running process "
                f"'{running}' ({current.__class__.__name__}).\n"
                '• Tasks must not call other tasks directly inside a '
                '@task/@task.calcfunction/@task.workfunction body.\n\n'
                'Do one of the following instead:\n'
                '  1) Compose tasks in a @task.graph function (build a graph and connect tasks), or\n'
                '  2) Move shared logic into a plain Python helper function and call that.'
            )

        outputs = super().__call__(*args, **kwargs)
        # if "metadata.call_link_label" is set, use it as the name of the task
        if outputs._task.inputs.metadata.call_link_label.value is not None:
            from aiida.workgraph.utils import _validate_task_name

            graph = outputs._graph
            new_name = outputs._task.inputs.metadata.call_link_label.value
            # `call_link_label` overrides the (already validated) function-derived name, so it
            # must be validated too; otherwise an invalid override slips past `add_task` and
            # only fails silently inside the engine at run time (see issue #784).
            _validate_task_name(new_name, source='call_link_label')
            outputs._task.name = new_name
            # update the names of tasks and links collections in the graph
            graph.tasks._items = {task.name: task for task in graph.tasks._items.values()}
            graph.links._items = {link.name: link for link in graph.links._items.values()}

        return outputs

    def run(self, /, *args, **kwargs):
        graph = self.build(*args, **kwargs)
        return graph.run()

    def run_get_graph(self, /, *args, **kwargs):
        graph = self.build(*args, **kwargs)
        return graph.run(), graph

    def submit(self, /, *args, **kwargs):
        graph = self.build(*args, **kwargs)
        graph.submit()
        return graph
