from __future__ import annotations
from uuid import uuid1
from aiida.node_graph.registry import RegistryHub, registry_hub
from typing import List, Optional, Dict, Any, Union, Callable
from aiida.node_graph.utils import deep_copy_only_dicts
from .socket import WaitingOn, TaskSocketNamespace
from node_graph_widget import NodeGraphWidget
from aiida.node_graph.collection import (
    PropertyCollection,
)
from .executor import SafeExecutor, BaseExecutor
from .error_handler import ErrorHandlerSpec
from aiida.node_graph.socket_spec import SocketSpecAPI
from .config import BuiltinPolicy
from .task_spec import TaskSpec
from dataclasses import replace
from .mixins import IOOwnerMixin, WidgetRenderableMixin, WaitableMixin


class Task(WidgetRenderableMixin, IOOwnerMixin, WaitableMixin):
    """Base class for Task.

    Attributes:
        identifier (str): The identifier is used for loading the Task.
        task_type (str): Type of this task. Possible values are "Normal", "REF", "GROUP".

    Examples:
        Add tasks:
        >>> float1 = ng.add_task("TestFloat", name="float1")
        >>> add1 = ng.add_task("TestDelayAdd", name="add1")

        Copy task:
        >>> n = task.copy(name="new_name")

        Append task to task graph:
        >>> ng.append_task(task)

    """

    _REGISTRY: Optional[RegistryHub] = registry_hub
    _PROPERTY_CLASS = PropertyCollection
    _SOCKET_SPEC_API = SocketSpecAPI
    _BUILTINS_POLICY = BuiltinPolicy()

    _default_spec = TaskSpec(
        identifier="node_graph.task",
        task_type="Normal",
        inputs=_SOCKET_SPEC_API.namespace(),
        outputs=_SOCKET_SPEC_API.namespace(),
        catalog="Base",
        base_class_path="node_graph.task.Task",
    )

    def __init__(
        self,
        name: Optional[str] = None,
        uuid: Optional[str] = None,
        graph: Optional["Graph"] = None,
        spec: Optional[TaskSpec] = None,
        parent: Optional[Task] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the Task.

        Args:
            name (str, optional): Name of the task. Defaults to None.
            uuid (str, optional): UUID of the task. Defaults to None.
            graph (Any, optional): The task graph this task belongs to. Defaults to None.
        """

        self.spec = spec or self._default_spec
        self.identifier = self.spec.identifier
        self.task_type = self.spec.task_type
        self.name = name or self.spec.identifier
        self.uuid = uuid or str(uuid1())
        self.graph = graph
        self.parent = parent
        self._metadata = metadata or {}
        self.properties = self._PROPERTY_CLASS(self, pool=self._REGISTRY.property_pool)

        self.state = "CREATED"
        self.action = "NONE"
        self.position = [30, 30]
        self.description = ""
        self.log = ""

        # Materialize the runtime objects from the spec
        self._materialize_from_spec()

        self.create_properties()
        # call update_spec once for the properties to take effect
        # in case the the properties has callback to update the spec
        self.update_spec()

        self._args_data = None
        self._widget = None
        self._waiting_on = WaitingOn(task=self, graph=self.graph)
        self._input_resolver: Optional[
            Callable[[Any], Any]
        ] = self._default_input_resolver
        self._allow_input_overrides = False

    def _materialize_from_spec(self) -> None:
        """
        Builds the runtime properties and sockets from the current self.spec.
        This is the bridge between the static definition (spec) and the live object.
        """
        # Materialize IO from spec
        input_spec = self.spec.inputs or self._SOCKET_SPEC_API.namespace()
        output_spec = self.spec.outputs or self._SOCKET_SPEC_API.namespace()
        if input_spec is not None:
            self.inputs = self._SOCKET_SPEC_API.SocketNamespace._from_spec(
                "inputs", input_spec, task=self, graph=self.graph, role="input"
            )
        if output_spec is not None:
            self.outputs = self._SOCKET_SPEC_API.SocketNamespace._from_spec(
                "outputs", output_spec, task=self, graph=self.graph, role="output"
            )

        self._ensure_builtins()

    def _ensure_builtins(self) -> None:
        """Create built-in sockets based on policy."""
        from aiida.node_graph.config import (
            WAIT_SOCKET_NAME,
            OUTPUT_SOCKET_NAME,
            MAX_LINK_LIMIT,
        )

        if self._BUILTINS_POLICY.input_wait and WAIT_SOCKET_NAME not in self.inputs:
            self.add_input(
                self._REGISTRY.socket_pool.any,
                WAIT_SOCKET_NAME,
                link_limit=MAX_LINK_LIMIT,
                metadata={
                    "required": False,
                    "arg_type": "none",
                    "builtin_socket": True,
                },
            )
        if (
            self._BUILTINS_POLICY.default_output
            and OUTPUT_SOCKET_NAME not in self.outputs
        ):
            self.add_output(
                self._REGISTRY.socket_pool.any,
                OUTPUT_SOCKET_NAME,
                metadata={"required": False, "builtin_socket": True},
            )
        if self._BUILTINS_POLICY.output_wait and WAIT_SOCKET_NAME not in self.outputs:
            self.add_output(
                self._REGISTRY.socket_pool.any,
                WAIT_SOCKET_NAME,
                link_limit=MAX_LINK_LIMIT,
                metadata={"required": False, "builtin_socket": True},
            )

    @property
    def widget(self) -> NodeGraphWidget:
        if self._widget is None:
            self._widget = NodeGraphWidget(
                settings={"minmap": False},
                style={"width": "80%", "height": "600px"},
            )
        return self._widget

    def add_property(self, identifier: str, name: str, **kwargs) -> Any:
        prop = self.properties._new(identifier, name, **kwargs)
        return prop

    def get_property_names(self) -> List[str]:
        return self.properties._get_keys()

    def create_properties(self) -> None:
        """Create properties for this task."""

    def update_spec(self) -> None:
        """Create input and output sockets for this task."""
        pass

    def reset(self) -> None:
        """Reset this task and all its child tasks to "CREATED"."""

    def to_dict(
        self, include_sockets: bool = False, should_serialize: bool = False
    ) -> Dict[str, Any]:
        """Save all datas, include properties, input and output sockets."""

        metadata = self.get_metadata()
        properties = self.export_properties()
        inputs_value = self.inputs._value
        if should_serialize and type(self).serialize_data is Task.serialize_data:
            inputs_value = self.inputs._collect_values(serialize=True)
        data = {
            "identifier": self.identifier,
            "uuid": self.uuid,
            "name": self.name,
            "state": self.state,
            "action": self.action,
            "error": "",
            "metadata": metadata,
            "spec": self.spec.to_dict(),
            "properties": properties,
            "inputs": inputs_value,
            "position": self.position,
            "description": self.description,
            "log": self.log,
            "hash": "",  # we can only calculate the hash during runtime when all the data is ready
            "input_socket_meta": self._export_input_socket_updatable_meta(),
        }
        if include_sockets:
            data["input_sockets"] = self.inputs._to_dict()
            data["output_sockets"] = self.outputs._to_dict()
        data["parent_task"] = [self.parent.name] if self.parent else [None]

        return data

    def serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize the task for database storage.
        This should be overrided by the subclass."""
        pass

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.get_metadata()

    def get_metadata(self) -> Dict[str, Any]:
        """Export metadata to a dictionary."""
        metadata = self._metadata.copy()
        return metadata

    @property
    def args_data(self) -> Dict[str, List]:
        if self._args_data is None:
            self._args_data = self.get_args_data()
        return self._args_data

    def get_args_data(self) -> Dict[str, List]:
        """Get all the args data from properties and inputs."""
        from aiida.node_graph.utils import get_arg_type

        args_data = {
            "args": [],
            "kwargs": [],
            "var_args": None,
            "var_kwargs": None,
        }
        for prop in self.properties:
            get_arg_type(prop.name, args_data, prop.arg_type)
        for input in self.inputs:
            get_arg_type(
                input._name,
                args_data,
                input._metadata.arg_type,
            )
        return args_data

    def export_properties(self) -> List[Dict[str, Any]]:
        """Export properties to a dictionary.
        This data will be used for calculation.
        """
        properties = {}
        for prop in self.properties:
            properties[prop.name] = prop.to_dict()
        return properties

    def export_executor_to_dict(self) -> Optional[Dict[str, Union[str, bool]]]:
        """Export executor to a dictionary.
        Three kinds of executor:
        - Python built-in function. e.g. getattr
        - User defined function
        - User defined class.
        """
        executor = self.get_executor()
        if executor is None:
            return executor
        if isinstance(executor, dict):
            executor = SafeExecutor(**executor)
        return executor.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any], graph: "Graph" = None) -> Any:
        """
        Factory method to rebuild a Task from dict data, handling persistence modes.
        """
        if "spec" in data:
            spec_dict = data["spec"]
            spec = TaskSpec.from_dict(spec_dict)
            task = spec.to_task(name=data["name"], graph=graph, uuid=data.get("uuid"))
            graph.tasks._append(task)
        else:
            identifier = data["metadata"]["identifier"]
            task = graph.add_task(
                identifier,
                name=data["name"],
                uuid=data.pop("uuid", None),
            )
        # then load the properties
        task.update_from_dict(data)
        return task

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """udpate task from dict data. Set metadata and properties.
        This method can be overrided.
        """

        for key in ["uuid", "state", "action", "description", "hash", "position"]:
            if data.get(key):
                setattr(self, key, data.get(key))
        # properties first, because the socket may be dynamic
        for name, prop in data.get("properties", {}).items():
            self.properties[name].value = prop["value"]
        # inputs
        self.inputs._set_socket_value(data.get("inputs", {}))
        if "input_socket_meta" in data:
            self._apply_input_socket_updatable_meta(data["input_socket_meta"])

    @classmethod
    def load(cls, uuid: str) -> None:
        """Load Task data from database."""

    @classmethod
    def new(
        cls,
        identifier: str,
        name: Optional[str] = None,
        TaskPool: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Create a task from a identifier.
        When a plugin create a task, it should provide its own task pool.
        Then call super().new(identifier, name, TaskPool) to create a task.
        """
        from aiida.node_graph.collection import get_item_class

        if TaskPool is None:
            from aiida.node_graph.tasks import TaskPool

        ItemClass = get_item_class(identifier, TaskPool)
        task = ItemClass(name=name, metadata=metadata)
        return task

    def _new_for_copy(
        self, name: Optional[str], graph: Optional[Any], spec: TaskSpec
    ) -> Any:
        """Factory hook used by copy(); subclasses can override to supply ctor args."""
        return self.__class__(name=name, uuid=None, graph=graph, spec=spec)

    def copy(
        self,
        name: Optional[str] = None,
        graph: Optional[Any] = None,
    ) -> Any:
        """Copy a task.

        Copy a task to a new task. If graph is None, the task will be copied inside the same graph,
        otherwise the task will be copied to a new graph.
        The properties, inputs and outputs will be copied.

        Args:
            name (str, optional): _description_. Defaults to None.
            graph (Graph, optional): _description_. Defaults to None.

        Returns:
            Task: _description_
        """
        if graph is not None:
            # copy task to a new graph, keep the name
            name = self.name if name is None else name
        else:
            # copy task inside the same graph, change the name
            graph = self.graph
            name = f"{self.name}_copy" if name is None else name
        task = self._new_for_copy(name=name, graph=graph, spec=self.spec)
        # becareful when copy the properties, the value should be copied
        # it will update the sockets, so we copy the properties first
        # then overwrite the sockets
        for i in range(len(self.properties)):
            task.properties[i].value = self.properties[i].value
        task.inputs._set_socket_value(self.inputs._value)
        task._apply_input_socket_updatable_meta(
            self._export_input_socket_updatable_meta()
        )
        return task

    def get_executor(self) -> Optional[BaseExecutor]:
        """Get the default executor."""
        return self.spec.executor

    @property
    def error_handlers(self) -> Dict[str, ErrorHandlerSpec]:
        return self.get_error_handlers()

    def get_error_handlers(self) -> Dict[str, ErrorHandlerSpec]:
        """Get the error handlers."""
        error_handlers = self.spec.error_handlers or {}
        error_handlers.update(self.spec.attached_error_handlers or {})
        return error_handlers

    def add_error_handler(self, error_handler: ErrorHandlerSpec | dict) -> None:
        """Add an error handler to this task."""
        from aiida.node_graph.error_handler import normalize_error_handlers

        error_handlers = normalize_error_handlers(error_handler)
        attached_error_handlers = self.spec.attached_error_handlers or {}
        attached_error_handlers.update(error_handlers)
        self.spec = replace(self.spec, attached_error_handlers=attached_error_handlers)

    def execute(self):
        """Execute the task."""
        executor = self.resolve_executor_callable(require=True)
        inputs = self.inputs._value
        args = [inputs[arg] for arg in self.args_data["args"]]
        kwargs = {key: inputs[key] for key in self.args_data["kwargs"]}
        var_kwargs = (
            inputs[self.args_data["var_kwargs"]]
            if self.args_data["var_kwargs"]
            else None
        )
        if var_kwargs is None:
            result = executor(*args, **kwargs)
        else:
            result = executor(*args, **kwargs, **var_kwargs)
        return result

    def resolve_executor_callable(self, *, require: bool = False):
        """Return the runtime callable, unwrapping handle wrappers when needed."""
        from aiida.node_graph.task_spec import BaseHandle

        executor_spec = self.get_executor()
        executor = executor_spec.callable if executor_spec is not None else None
        if isinstance(executor, BaseHandle) and hasattr(executor, "_callable"):
            executor = getattr(executor, "_callable")
        if require and executor is None:
            raise RuntimeError(f"No executor callable available for {self.identifier}.")
        return executor

    def get_results(self) -> None:
        """Item data from database"""

    def update(self) -> None:
        """Update task state."""

    @property
    def results(self) -> None:
        return self.get_results()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name='{self.name}', properties=[{', '.join(repr(k) for k in self.get_property_names())}], "
            f"inputs=[{', '.join(repr(k) for k in self.get_input_names())}], "
            f"outputs=[{', '.join(repr(k) for k in self.get_output_names())}])"
        )

    def set_inputs(
        self, data: Dict[str, Any], *, value_source: Optional[str] = None
    ) -> None:
        """Set properties by a dict.

        Args:
            data (dict): Input values keyed by socket/property name.
            value_source (str, optional): "link" to prefer linked values,
                or "property" to force property values even when linked.
        """

        data = deep_copy_only_dicts(data)
        if value_source is None:
            value_source = "property" if self._allow_input_overrides else "link"
        if value_source not in ("link", "property"):
            raise ValueError(
                "value_source must be 'link' or 'property'; got " f"{value_source!r}."
            )
        for key, value in data.items():
            # if the value is a task, link the task's top-level output to the input
            if value is None:
                continue
            if isinstance(value, Task):
                self.graph.add_link(value.outputs["_outputs"], self.inputs[key])
                continue
            if key in self.properties:
                self.properties[key].value = value
            else:
                self.inputs._set_socket_value({key: value}, value_source=value_source)

    def set_input_resolver(self, resolver: Optional[Callable[[Any], Any]]) -> None:
        """Set a resolver for input socket values."""
        self._input_resolver = resolver

    def clear_input_resolver(self) -> None:
        self._input_resolver = None

    def _default_input_resolver(self, socket: Any) -> Any:
        """Resolve inputs using raw literals or upstream socket values."""
        if isinstance(socket, TaskSocketNamespace):
            raw_value = socket._collect_values(resolve=False)
        else:
            raw_value = socket._value

        links = [
            link
            for link in getattr(socket, "_links", [])
            if getattr(link, "to_socket", None) is socket
        ]
        if not links:
            return raw_value

        active_links = [lk for lk in links if lk.from_socket._scoped_name != "_wait"]
        if not active_links:
            return raw_value

        if len(active_links) == 1:
            from_socket = active_links[0].from_socket
            if from_socket._scoped_name == "_outputs":
                return from_socket._task.outputs._collect_values(resolve=False)
            if isinstance(from_socket, TaskSocketNamespace):
                return from_socket._collect_values(resolve=False)
            return from_socket._value

        bundle = {}
        for lk in active_links:
            from_socket = lk.from_socket
            key = f"{lk.from_task.name}_{from_socket._scoped_name}"
            if from_socket._scoped_name == "_outputs":
                bundle[key] = from_socket._task.outputs._collect_values(resolve=False)
            elif isinstance(from_socket, TaskSocketNamespace):
                bundle[key] = from_socket._collect_values(resolve=False)
            else:
                bundle[key] = from_socket._value
        return bundle or raw_value

    def _export_input_socket_updatable_meta(self) -> Dict[str, Dict[str, Any]]:
        """Export updatable metadata for input sockets."""
        return self.inputs._export_updatable_meta_map()

    def _apply_input_socket_updatable_meta(
        self, meta_map: Dict[str, Dict[str, Any]]
    ) -> None:
        """Apply updatable metadata for input sockets."""
        if not meta_map:
            return
        self.inputs._apply_updatable_meta_map(meta_map)

    def get(self, key: str) -> Any:
        """Get the value of property by key.

        Args:
            key (_type_): _description_

        Returns:
            _type_: _description_
        """
        return self.properties[key].value

    def save(self) -> None:
        """Modify and save a task to database."""

    def to_widget_value(self):
        tdata = self.to_dict(include_sockets=True)

        for key in ("properties", "executor", "task_class", "process", "input_values"):
            tdata.pop(key, None)
        inputs = []
        for input in tdata["input_sockets"]["sockets"].values():
            input.pop("property", None)
            inputs.append(input)

        tdata["inputs"] = inputs

        tdata["label"] = tdata["identifier"]

        wgdata = {"name": self.name, "nodes": {self.name: tdata}, "links": []}
        return wgdata


class TaskSet:
    """
    A collection of tasks that belong to a specific parent task.

    This class provides an interface for managing a set of tasks, allowing
    tasks to be added, removed, and iterated over while maintaining a reference
    to their parent task and ensuring they exist within a valid task graph.

    """

    def __init__(self, parent: "Task"):
        self._items: Set[str] = set()
        self.parent = parent

    @property
    def graph(self) -> "Graph":
        """Cache and return the graph of the parent task."""
        return self.parent.graph

    @property
    def items(self) -> Set[str]:
        return self._items

    def _normalize_tasks(
        self, tasks: Union[List[Union[str, Task]], str, Task]
    ) -> Iterable[str]:
        """Normalize input to an iterable of task names."""
        if isinstance(tasks, (str, Task)):
            tasks = [tasks]
        task_objects = []
        for task in tasks:
            if isinstance(task, str):
                if task not in self.graph.tasks:
                    raise ValueError(
                        f"Task '{task}' is not in the graph. Available tasks: {self.graph.tasks}"
                    )
                task_objects.append(self.graph.tasks[task])
            elif isinstance(task, Task):
                task_objects.append(task)
            else:
                raise ValueError(f"Invalid task type: {type(task)}")
        return task_objects

    def add(self, tasks: Union[List[Union[str, Task]], str, Task]) -> None:
        """Add tasks to the collection. Tasks can be a list or a single Task or task name."""
        # If the task does not belong to any graph, skip adding it
        if isinstance(self.graph, Task):
            return
        normalize_tasks = []
        for task in self._normalize_tasks(tasks):
            self._items.add(task)
            normalize_tasks.append(task)
        return normalize_tasks

    def remove(self, tasks: Union[List[Union[str, Task]], str, Task]) -> None:
        """Remove tasks from the collection. Tasks can be a list or a single Task or task name."""
        for task in self._normalize_tasks(tasks):
            if task not in self._items:
                raise ValueError(f"Task '{task.name}' is not in the collection.")
            self._items.remove(task)

    def clear(self) -> None:
        """Clear all items from the collection."""
        self._items.clear()

    def __contains__(self, item: str) -> bool:
        """Check if a task name is in the collection."""
        return item in self._items

    def __iter__(self):
        """Yield each task name in the collection for iteration."""
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return f"{self._items}"


# collection of child tasks
class ChildTaskSet(TaskSet):
    def add(self, tasks: Union[List[Union[str, Task]], str, Task]) -> None:
        """Add tasks to the collection. Tasks can be a list or a single Task or task name."""
        normalize_tasks = super().add(tasks)
        for task in normalize_tasks:
            if task.parent is not None:
                raise ValueError("Task is already a child of the task: {task.parent}")
            task.parent = self.parent
