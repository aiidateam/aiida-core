from __future__ import annotations
from aiida.node_graph.registry import RegistryHub, registry_hub
from aiida.node_graph.collection import TaskCollection, LinkCollection
from uuid import uuid1
from aiida.node_graph.task_spec import TaskSpec
from aiida.node_graph.socket_spec import SocketSpec, SocketSpecAPI
from typing import Dict, Any, List, Optional, Union, Callable
import yaml
from aiida.node_graph.task import Task
from aiida.node_graph.socket import TaskSocket, TaskSocketNamespace
from aiida.node_graph.link import TaskLink
from aiida.node_graph.utils import yaml_to_dict
from .config import (
    BuiltinPolicy,
    BUILTIN_TASKS,
    INPUT_SOCKET_NAME,
    MAX_LINK_LIMIT,
    OUTPUT_SOCKET_NAME,
)
from .mixins import IOOwnerMixin, WidgetRenderableMixin
from aiida.node_graph.knowledge import KnowledgeGraph
from dataclasses import dataclass
from dataclasses import replace


@dataclass(frozen=True)
class GraphSpec:
    """Specification for a Graph's inputs and outputs."""

    schema_source: str = "EMBEDDED"
    inputs: Optional[SocketSpec] = None
    outputs: Optional[SocketSpec] = None
    ctx: Optional[SocketSpec] = None

    def __post_init__(self):
        # ctx should be dynamic
        if self.ctx is not None and not self.ctx.dynamic:
            object.__setattr__(self, "ctx", replace(self.ctx, dynamic=True))

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"schema_source": self.schema_source}
        if self.inputs is not None:
            data["inputs"] = self.inputs.to_dict()
        if self.outputs is not None:
            data["outputs"] = self.outputs.to_dict()
        if self.ctx is not None:
            data["ctx"] = self.ctx.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphSpec":
        from aiida.node_graph.socket_spec import SocketSpec

        inputs = SocketSpec.from_dict(data["inputs"]) if "inputs" in data else None
        outputs = SocketSpec.from_dict(data["outputs"]) if "outputs" in data else None
        ctx = SocketSpec.from_dict(data["ctx"]) if "ctx" in data else None
        return cls(
            schema_source=data.get("schema_source", "EMBEDDED"),
            inputs=inputs,
            outputs=outputs,
            ctx=ctx,
        )


class Graph(IOOwnerMixin, WidgetRenderableMixin):
    """A collection of tasks and links.

    Attributes:
        name (str): The name of the task graph.
        uuid (str): The UUID of this task graph.
        graph_type (str): The type of the task graph.
        state (str): The state of this task graph.
        action (str): The action of this task graph.
        platform (str): The platform used to create this task graph.
        description (str): A description of the task graph.

    Examples:
        >>> from node_graph import Graph
        >>> ng = Graph(name="my_first_taskgraph")

        Add tasks:
        >>> float1 = ng.add_task("node_graph.test_float", name="float1")
        >>> add1 = ng.add_task("node_graph.test_add", name="add1")

        Add links:
        >>> ng.add_link(float1.outputs[0], add1.inputs[0])

        Export to dict:
        >>> ng.to_dict()
    """

    _REGISTRY: Optional[RegistryHub] = registry_hub
    _BUILTINS_POLICY = BuiltinPolicy()
    _SOCKET_SPEC_API = SocketSpecAPI

    platform: str = "node_graph"

    def __init__(
        self,
        name: str = "Graph",
        inputs: Optional[SocketSpec | List[str]] = None,
        outputs: Optional[SocketSpec | List[str]] = None,
        ctx: Optional[SocketSpec | List[str]] = None,
        uuid: Optional[str] = None,
        graph_type: str = "NORMAL",
        graph: Optional[Graph] = None,
        parent: Optional[Task] = None,
        interactive_widget: bool = False,
        init_graph_level_tasks: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        serialization: Optional[object] = None,
        serialization_policy: str = "off",
    ) -> None:
        """Initializes a new instance of the Graph class.

        Args:
            name (str, optional): The name of the task graph. Defaults to "Graph".
            uuid (str, optional): The UUID of the task graph. Defaults to None.
            graph_type (str, optional): The type of the task graph. Defaults to "NORMAL".
        """

        self.name = name
        self.uuid = uuid or str(uuid1())
        self.graph_type = graph_type
        self.graph = graph
        self.parent = parent
        self.type_mapping = dict(self._REGISTRY.type_mapping)
        self.type_promotions = set(self._REGISTRY.type_promotion)
        self.tasks = TaskCollection(graph=self, pool=self._REGISTRY.task_pool)
        self.links = LinkCollection(self)
        self._widget = None
        self.interactive_widget = interactive_widget
        self._version = 0  # keep track the changes
        if serialization_policy not in {"off", "validate", "eager"}:
            raise ValueError(
                "serialization_policy must be one of: off, validate, eager"
            )
        if serialization is None:
            from aiida.node_graph.serializer import NullSerializationAdapter

            serialization = NullSerializationAdapter()
        self.serialization = serialization
        self.serialization_policy = serialization_policy
        self._init_graph_spec(inputs, outputs, ctx)
        if init_graph_level_tasks:
            self._init_graph_level_tasks()
        self.knowledge_graph = KnowledgeGraph(graph_uuid=self.uuid, graph=self)
        self._metadata: Dict[str, Any] = dict(metadata or {})

        self.state = "CREATED"
        self.action = "NONE"
        self.description = ""

    def _init_graph_spec(
        self,
        inputs: Optional[SocketSpec],
        outputs: Optional[SocketSpec],
        ctx: Optional[SocketSpec],
    ) -> None:

        inputs = self._SOCKET_SPEC_API.validate_socket_data(inputs)
        # if inputs is None, we assume it's a dynamic inputs
        inputs = self._SOCKET_SPEC_API.dynamic() if inputs is None else inputs
        meta = replace(inputs.meta, child_default_link_limit=MAX_LINK_LIMIT)
        inputs = replace(inputs, meta=meta)
        outputs = self._SOCKET_SPEC_API.validate_socket_data(outputs)
        # if outputs is None, we assume it's a dynamic outputs
        outputs = self._SOCKET_SPEC_API.dynamic() if outputs is None else outputs
        ctx = self._SOCKET_SPEC_API.validate_socket_data(ctx)
        # if ctx is None, we assume it's a dynamic ctx
        ctx = self._SOCKET_SPEC_API.dynamic() if ctx is None else ctx
        self.spec = GraphSpec(inputs=inputs, outputs=outputs, ctx=ctx)

    def _init_graph_level_tasks(self):
        base_class = self._REGISTRY.task_pool["graph_level"].load()
        self.graph_inputs_spec = TaskSpec(
            identifier="graph_inputs",
            inputs=self.spec.inputs,
            base_class=base_class,
        )
        self.tasks._new(self.graph_inputs_spec, name="graph_inputs")

        self.graph_outputs_spec = TaskSpec(
            identifier="graph_outputs",
            inputs=self.spec.outputs,
            base_class=base_class,
        )
        graph_outputs = self.tasks._new(self.graph_outputs_spec, name="graph_outputs")
        graph_outputs.inputs._name = "outputs"
        # graph context
        ctx = self.spec.ctx or self._SOCKET_SPEC_API.dynamic(Any)
        meta = replace(ctx.meta, child_default_link_limit=1000000)
        ctx = replace(ctx, meta=meta)
        self.spec = replace(self.spec, ctx=ctx)
        self.graph_ctx_spec = TaskSpec(
            identifier="graph_ctx",
            inputs=ctx,
            base_class=base_class,
        )
        graph_ctx = self.tasks._new(self.graph_ctx_spec, name="graph_ctx")
        graph_ctx.inputs._name = "ctx"

    @property
    def graph_inputs(self) -> Task:
        """Group inputs task."""
        return self.tasks["graph_inputs"]

    @property
    def graph_outputs(self) -> Task:
        """Group outputs task."""
        return self.tasks["graph_outputs"]

    @property
    def graph_ctx(self) -> Task:
        """Context variable task."""
        return self.tasks["graph_ctx"]

    @property
    def inputs(self) -> Task:
        """Group inputs task."""
        return self.graph_inputs.inputs

    @inputs.setter
    def inputs(self, value: Dict[str, Any]) -> None:
        """Set group inputs task."""
        self.graph_inputs.inputs._set_socket_value(value)

    @property
    def outputs(self) -> Task:
        """Group outputs task."""
        return self.graph_outputs.inputs

    @outputs.setter
    def outputs(self, value: Dict[str, Any]) -> None:
        """Set group outputs task."""
        self.graph_outputs.inputs._set_socket_value(value)

    @property
    def ctx(self) -> Task:
        """Context task."""
        return self.graph_ctx.inputs

    @ctx.setter
    def ctx(self, value: Dict[str, Any]) -> None:
        """Set context task."""
        self.graph_ctx.inputs._clear()
        self.graph_ctx.inputs._set_socket_value(value)

    def update_ctx(self, value: Dict[str, Any]) -> None:
        self.ctx._set_socket_value(value)

    def expose_inputs(self, names: Optional[List[str]] = None) -> None:
        """Generate group inputs from tasks."""
        all_names = set(self.tasks._get_keys())
        names = set(names or all_names)
        missing = names - all_names
        if missing:
            raise ValueError(f"The following tasks do not exist: {missing}")
        for name in names - set(BUILTIN_TASKS):
            task = self.tasks[name]
            # update the _inputs spec
            if task.spec.inputs is not None:
                socket = self.add_input_spec(task.spec.inputs, name=task.name)
                # add link from group inputs to task inputs
                self.add_link(
                    socket,
                    task.inputs,
                    allow_skip_linked=True,
                )

    def expose_outputs(self, names: Optional[List[str]] = None) -> None:
        """Generate group outputs from tasks."""
        all_names = set(self.tasks._get_keys())
        names = set(names or all_names)
        missing = names - all_names
        if missing:
            raise ValueError(f"The following tasks do not exist: {missing}")
        for name in names - set(BUILTIN_TASKS):
            task = self.tasks[name]
            if task.spec.outputs is not None:
                socket = self.add_output_spec(task.spec.outputs, name=task.name)
                # add link from task outputs to group outputs
                self.add_link(
                    task.outputs,
                    socket,
                    allow_skip_linked=True,
                )

    def set_inputs(self, inputs: Dict[str, Any]):
        for name, input in inputs.items():
            if "graph_inputs" in self.tasks and name in self.inputs:
                setattr(self.inputs, name, input)
            elif name in self.tasks:
                self.tasks[name].set_inputs(input)
            else:
                raise KeyError(
                    f"{name} does not exist. Accepted keys are: {list(self.get_task_names()) + ['graph_inputs']}."
                )

    @property
    def platform_version(self) -> str:
        """Retrieve the platform version dynamically from the package where Graph is implemented."""
        import importlib.metadata

        try:
            package_name = self.platform.replace("-", "_")
            return importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            return "unknown"

    def add_task(
        self,
        identifier: Union[str, Callable],
        name: str = None,
        include_builtins: bool = False,
        **kwargs,
    ) -> Task:
        """Adds a task to the task graph."""

        from aiida.node_graph.decorator import build_task_from_callable
        from aiida.node_graph.task_spec import TaskHandle
        from aiida.node_graph.tasks.subgraph_task import _build_subgraph_task_taskspec

        if name in BUILTIN_TASKS and not include_builtins:
            raise ValueError(f"Name {name} can not be used, it is reserved.")

        if isinstance(identifier, Graph):
            identifier = _build_subgraph_task_taskspec(graph=identifier, name=name)
        # build the task on the fly if the identifier is a callable
        elif callable(identifier) and not isinstance(
            identifier, (TaskSpec, TaskHandle)
        ):
            identifier = build_task_from_callable(identifier)
        task = self.tasks._new(identifier, name, **kwargs)
        self._version += 1
        return task

    def add_link(
        self,
        source: TaskSocket | Task,
        target: TaskSocket | "TaskSocketNamespace",
        *,
        allow_skip_linked: bool = False,
    ) -> TaskLink | None:
        """Add a link between two sockets or namespace sockets.

        When linking namespaces, all leaf sockets are linked recursively and a
        namespace-level link is also created for bookkeeping. Set
        allow_skip_linked=True to skip targets that are already linked.
        """
        from aiida.node_graph.socket import TaskSocketNamespace

        source, target = self._normalize_link_endpoints(source, target)

        if isinstance(source, TaskSocketNamespace) or isinstance(
            target, TaskSocketNamespace
        ):
            if isinstance(source, TaskSocketNamespace) and isinstance(
                target, TaskSocketNamespace
            ):
                if not self._namespace_structures_match(source, target):
                    source_keys = source._relative_keys()
                    target_keys = target._relative_keys()
                    src = source._full_name_with_task
                    dst = target._full_name_with_task
                    raise ValueError(
                        "Namespace structures do not match for linking: "
                        f"{src} vs {dst}. "
                        f"Missing in source: {sorted(target_keys - source_keys)}. "
                        f"Missing in target: {sorted(source_keys - target_keys)}."
                    )
                return self._add_namespace_link(
                    source, target, allow_skip_linked=allow_skip_linked
                )
            if (
                isinstance(target, TaskSocketNamespace)
                and target._metadata.dynamic
                and not isinstance(source, TaskSocketNamespace)
            ):
                return self._add_leaf_link(source, target)
            if (
                isinstance(target, TaskSocketNamespace)
                and not isinstance(source, TaskSocketNamespace)
                and getattr(source, "_scoped_name", None) == OUTPUT_SOCKET_NAME
            ):
                return self._add_leaf_link(source, target)
            if isinstance(source, TaskSocketNamespace):
                normalized = self._normalize_namespace_source(source)
                if normalized is None:
                    src = getattr(source, "_full_name_with_task", "<unknown>")
                    dst = getattr(target, "_full_name_with_task", "<unknown>")
                    raise TypeError(
                        "Linking a namespace socket directly to a leaf socket is not allowed. "
                        f"Got {src} -> {dst}."
                    )
                return self._add_leaf_link(normalized, target)
            src = getattr(source, "_full_name_with_task", "<unknown>")
            dst = getattr(target, "_full_name_with_task", "<unknown>")
            raise TypeError(
                "Linking a namespace socket directly to a leaf socket is not allowed. "
                f"Got {src} -> {dst}."
            )
        #
        return self._add_leaf_link(source, target)

    def _normalize_link_endpoints(
        self,
        source: TaskSocket | Task,
        target: TaskSocket | "TaskSocketNamespace",
    ) -> tuple[TaskSocket | "TaskSocketNamespace", TaskSocket | "TaskSocketNamespace"]:
        from aiida.node_graph.socket import TaskSocketNamespace

        if isinstance(source, Task):
            source = source.outputs["graph_outputs"]
        elif source._parent is None and isinstance(source, TaskSocketNamespace):
            if not isinstance(target, TaskSocketNamespace):
                # if the source is the top-level outputs,
                # we use the built-in outputs socket to represent it
                normalized = self._normalize_namespace_source(source)
                if normalized is None:
                    raise ValueError(
                        f"You try to link a top-level output socket {source._name} without a parent."
                    )
                source = normalized
        return source, target

    def _normalize_namespace_source(
        self, source: "TaskSocketNamespace"
    ) -> TaskSocket | "TaskSocketNamespace":
        if OUTPUT_SOCKET_NAME in source:
            return source[OUTPUT_SOCKET_NAME]
        return None

    def _link_key(
        self,
        source: TaskSocket | "TaskSocketNamespace",
        target: TaskSocket | "TaskSocketNamespace",
    ) -> str:
        return (
            f"{source._task.name}.{source._scoped_name} -> "
            f"{target._task.name}.{target._scoped_name}"
        )

    def _add_leaf_link(
        self,
        source: TaskSocket | "TaskSocketNamespace",
        target: TaskSocket | "TaskSocketNamespace",
    ) -> TaskLink:
        key = self._link_key(source, target)
        if key in self.links:
            return self.links[key]
        link = self.links._new(source, target)
        self._version += 1
        return link

    def _namespace_structures_match(
        self, source: "TaskSocketNamespace", target: "TaskSocketNamespace"
    ) -> bool:
        if source._metadata.dynamic or target._metadata.dynamic:
            return True
        return source._relative_keys() == target._relative_keys()

    def _has_incoming_links(self, item: TaskSocket | "TaskSocketNamespace") -> bool:
        """Return True if the target socket already has incoming links."""
        return any(link.to_socket is item for link in item._links)

    def _add_namespace_link(
        self,
        source: "TaskSocketNamespace",
        target: "TaskSocketNamespace",
        *,
        allow_skip_linked: bool = False,
    ) -> TaskLink | None:
        """Link two namespaces, optionally skipping already-linked targets."""
        from aiida.node_graph.socket import TaskSocketNamespace

        last_link: TaskLink | None = None
        link_source: TaskSocket | TaskSocketNamespace = source
        if source._parent is None and OUTPUT_SOCKET_NAME in source:
            link_source = source[OUTPUT_SOCKET_NAME]

        if not (allow_skip_linked and self._has_incoming_links(target)):
            key = self._link_key(link_source, target)
            if key in self.links:
                last_link = self.links[key]
            else:
                last_link = self._add_leaf_link(link_source, target)

        for name, target_child in target._iter_children(include_builtins=False):
            if name not in source._sockets:
                src = source._full_name_with_task
                dst = target._full_name_with_task
                raise ValueError(
                    f"Namespace link mismatch: '{name}' not found in source {src} "
                    f"while linking to {dst}."
                )
            source_child = source._sockets[name]
            if self._has_incoming_links(target_child):
                if allow_skip_linked:
                    continue
                src = source_child._full_name_with_task
                dst = target_child._full_name_with_task
                existing_link = next(
                    (
                        link
                        for link in target_child._links
                        if link.to_socket is target_child
                    ),
                    None,
                )
                if existing_link is not None:
                    existing_src = existing_link.from_socket._full_name_with_task
                    existing_dst = existing_link.to_socket._full_name_with_task
                    existing_desc = f"{existing_src} -> {existing_dst}"
                else:
                    existing_desc = "<unknown>"
                raise ValueError(
                    "Namespace link conflict: target socket already linked. "
                    f"Existing link: {existing_desc}. "
                    f"Attempted link: {src} -> {dst}. "
                    "Unlink the existing connection or pass allow_skip_linked=True "
                    "to ignore already-linked targets."
                )
            if isinstance(source_child, TaskSocketNamespace) and isinstance(
                target_child, TaskSocketNamespace
            ):
                child_link = self._add_namespace_link(
                    source_child,
                    target_child,
                    allow_skip_linked=allow_skip_linked,
                )
                if child_link is not None:
                    last_link = child_link
                continue
            if isinstance(source_child, TaskSocketNamespace) or isinstance(
                target_child, TaskSocketNamespace
            ):
                src = source_child._full_name_with_task
                dst = target_child._full_name_with_task
                raise TypeError(
                    "Namespace link mismatch: tried to link a namespace with a leaf "
                    f"socket at {src} -> {dst}."
                )
            last_link = self.add_link(source_child, target_child)
        return last_link

    def append_task(self, task: Task) -> None:
        """Appends a task to the task graph."""
        self.tasks._append(task)

    def get_task_names(self) -> List[str]:
        """Returns the names of the tasks in the task graph."""
        return self.tasks._get_keys()

    def launch(self) -> None:
        """Launches the task graph."""
        raise NotImplementedError("The 'launch' method is not implemented.")

    def wait(self) -> None:
        """Waits for the task graph to finish.

        Args:
            timeout (int, optional): The maximum time to wait in seconds. Defaults to 50.
        """
        return NotImplementedError("The 'wait' method is not implemented.")

    def save(self) -> None:
        """Saves the task graph to the database."""
        raise NotImplementedError("The 'save' method is not implemented.")

    def to_dict(
        self, include_sockets: bool = False, should_serialize: bool = False
    ) -> Dict[str, Any]:
        """Converts the task graph to a dictionary.

        Args:
            short (bool, optional): Indicates whether to include short task representations. Defaults to False.

        Returns:
            Dict[str, Any]: The task graph data.
        """
        # Capture the current ctx namespace shape into the graph spec before exporting.
        if hasattr(self.graph_ctx, "inputs"):
            ctx_snapshot = self.graph_ctx.inputs._to_spec()
            self.spec = replace(self.spec, ctx=ctx_snapshot)

        metadata = self.get_metadata()
        tasks = self.export_tasks_to_dict(
            include_sockets=include_sockets, should_serialize=should_serialize
        )

        links = self.links_to_dict()
        kg_payload = self.knowledge_graph.to_dict()

        data = {
            "platform_version": f"{self.platform}@{self.platform_version}",
            "uuid": self.uuid,
            "name": self.name,
            "state": self.state,
            "action": self.action,
            "error": "",
            "metadata": metadata,
            "spec": self.spec.to_dict(),
            "tasks": tasks,
            "links": links,
            "description": self.description,
            "knowledge_graph": kg_payload,
        }
        return data

    def get_metadata(self) -> Dict[str, Any]:
        """Export graph metadata including *live* graph-level IO specs."""
        meta: Dict[str, Any] = {
            "graph_type": self.graph_type,
        }
        # also save the parent class information
        meta["graph_class"] = {
            "callable_name": self.__class__.__name__,
            "module_path": self.__class__.__module__,
        }
        for key, value in (self._metadata or {}).items():
            if key in {"graph_type", "graph_class"}:
                continue
            meta[key] = value
        return meta

    def export_tasks_to_dict(
        self, include_sockets: bool = False, should_serialize: bool = False
    ) -> Dict[str, Any]:
        """Converts the tasks to a dictionary.

        Args:
            short (bool, optional): Indicates whether to include short task representations. Defaults to False.

        Returns:
            Dict[str, Any]: The tasks data.
        """
        # generate spec for graph-level tasks
        tasks = {}
        for task in self.tasks:
            tasks[task.name] = task.to_dict(
                include_sockets=include_sockets, should_serialize=should_serialize
            )
        return tasks

    def links_to_dict(self) -> List[Dict[str, Any]]:
        """Converts the links to a list of dictionaries.

        Returns:
            List[Dict[str, Any]]: The links data.
        """
        links = []
        for link in self.links:
            links.append(link.to_dict())
        return links

    def to_yaml(self) -> str:
        """Exports the task graph to a YAML format data.

        Results of the tasks are not exported.

        Returns:
            str: The YAML string representation of the task graph.
        """
        data: Dict[str, Any] = self.to_dict()
        for task in data["tasks"].values():
            task.pop("results", None)
        return yaml.dump(data, sort_keys=False)

    def update(self) -> None:
        """Updates the task graph from the database."""
        raise NotImplementedError("The 'update' method is not implemented.")

    def links_from_dict(self, links: list) -> None:
        """Adds links to the task graph from a dictionary.

        Args:
            links (List[Dict[str, Any]]): The links data.
        """
        from aiida.node_graph.socket import TaskSocketNamespace

        for link in links:
            from_task = self.tasks[link["from_task"]]
            from_socket = link["from_socket"]
            if from_socket == OUTPUT_SOCKET_NAME:
                source = from_task.outputs
            else:
                source = from_task.outputs[from_socket]
            task = self.tasks[link["to_task"]]
            socket_path = link["to_socket"]
            if socket_path == INPUT_SOCKET_NAME:
                target = task.inputs
                self.add_link(source, target, allow_skip_linked=True)
                continue
            if socket_path in task.inputs:
                target = task.inputs[socket_path]
            else:
                parts = socket_path.split(".")
                parent: TaskSocketNamespace | object = task.inputs
                for part in parts[:-1]:
                    if part in parent:
                        parent = parent[part]
                        if not isinstance(parent, TaskSocketNamespace):
                            raise ValueError(
                                f"Cannot create nested socket '{socket_path}' under leaf "
                                f"{parent._full_name_with_task}."
                            )
                        continue
                    if (
                        not isinstance(parent, TaskSocketNamespace)
                        or not parent._metadata.dynamic
                    ):
                        raise ValueError(
                            f"Missing socket '{socket_path}' in {task.name}.inputs and "
                            "parent namespace is not dynamic."
                        )
                    parent._append_dynamic_child(part, {})
                    parent = parent[part]
                if not isinstance(parent, TaskSocketNamespace):
                    raise ValueError(
                        f"Cannot create socket '{socket_path}' under leaf "
                        f"{parent._full_name_with_task}."
                    )
                if not parent._metadata.dynamic:
                    raise ValueError(
                        f"Missing socket '{socket_path}' in {task.name}.inputs and "
                        "parent namespace is not dynamic."
                    )
                if (
                    isinstance(source, TaskSocketNamespace)
                    or getattr(source, "_scoped_name", None) == OUTPUT_SOCKET_NAME
                ):
                    parent._append_dynamic_child(parts[-1], {})
                else:
                    parent._append_dynamic_child(parts[-1], None)
                target = parent[parts[-1]]
            self.add_link(source, target, allow_skip_linked=True)

    @classmethod
    def from_dict(cls, ngdata: Dict[str, Any]) -> Graph:
        """Rebuilds a task graph from a dictionary.

        Args:
            ngdata (Dict[str, Any]): The data of the task graph.

        Returns:
            Graph: The rebuilt task graph.
        """
        spec = GraphSpec.from_dict(ngdata.get("spec", {}))
        raw_meta = ngdata.get("metadata", {}) or {}
        base_meta = {k: raw_meta[k] for k in ("graph_type",) if k in raw_meta}
        extra_meta = {k: v for k, v in raw_meta.items() if k not in {"graph_type"}}
        ng = cls(
            name=ngdata["name"],
            uuid=ngdata.get("uuid"),
            inputs=spec.inputs,
            outputs=spec.outputs,
            ctx=spec.ctx,
            graph_type=base_meta.get("graph_type", "NORMAL"),
            metadata=extra_meta,
        )
        ng.state = ngdata.get("state", "CREATED")
        ng.action = ngdata.get("action", "NONE")
        ng.description = ngdata.get("description", "")

        for ndata in ngdata["tasks"].values():
            ng.add_task_from_dict(ndata)

        ng.links_from_dict(ngdata.get("links", []))
        kg_payload = ngdata.get("knowledge_graph")
        if kg_payload is not None:
            ng.knowledge_graph = KnowledgeGraph.from_dict(
                kg_payload, graph_uuid=ng.uuid
            )
            ng.knowledge_graph._graph = ng
            ng.knowledge_graph.graph_uuid = ng.uuid
            ng.knowledge_graph._dirty = True
        return ng

    def add_task_from_dict(self, ndata: Dict[str, Any]) -> Task:
        """Adds a task to the task graph from a dictionary.

        Args:
            ndata (Dict[str, Any]): The data of the task.

        Returns:
            Task: The added task.
        """

        name = ndata["name"]
        if name in BUILTIN_TASKS:
            self.tasks[name].update_from_dict(ndata)
            return self.tasks[name]
        else:
            return Task.from_dict(ndata, graph=self)

    @classmethod
    def from_yaml(
        cls, filename: Optional[str] = None, string: Optional[str] = None
    ) -> "Graph":
        """Builds a task graph from a YAML file or string.

        Args:
            filename (str, optional): The filename of the YAML file. Defaults to None.
            string (str, optional): The YAML string. Defaults to None.

        Raises:
            ValueError: If neither filename nor string is provided.

        Returns:
            Graph: The built task graph.
        """
        if filename:
            with open(filename, "r") as f:
                ngdata = yaml.safe_load(f)
        elif string:
            ngdata = yaml.safe_load(string)
        else:
            raise ValueError("Please specify a filename or YAML string.")
        ngdata = yaml_to_dict(ngdata)
        ng = cls.from_dict(ngdata)
        return ng

    def copy(self, name: Optional[str] = None) -> "Graph":
        """Copies the task graph.

        The tasks and links are copied.

        Args:
            name (str, optional): The name of the new task graph. Defaults to None.

        Returns:
            Graph: The copied task graph.
        """
        name = f"{self.name}_copy" if name is None else name
        ng = self.__class__(name=name, uuid=None)
        ng.tasks = self.tasks._copy(graph=ng)
        for link in self.links:
            ng.add_link(
                ng.tasks[link.from_task.name].outputs[link.from_socket._scoped_name],
                ng.tasks[link.to_task.name].inputs[link.to_socket._scoped_name],
            )
        ng.knowledge_graph = self.knowledge_graph.copy(graph_uuid=ng.uuid)
        ng.knowledge_graph._graph = ng
        return ng

    @classmethod
    def load(cls) -> None:
        """Loads data from the database."""
        raise NotImplementedError("The 'load' method is not implemented.")

    def copy_subset(
        self, task_list: List[str], name: Optional[str] = None, add_ref: bool = True
    ) -> "Graph":
        """Copies a subset of the task graph.

        Args:
            task_list (List[str]): The names of the tasks to be copied.
            name (str, optional): The name of the new task graph. Defaults to None.
            add_ref (bool, optional): Indicates whether to add reference tasks. Defaults to True.

        Returns:
            Graph: The new task graph.
        """
        ng: "Graph" = self.__class__(name=name, uuid=None)
        for task_name in task_list:
            ng.append_task(self.tasks[task_name].copy(graph=ng))
        for link in self.links:
            if (
                add_ref
                and link.from_task.name not in ng.get_task_names()
                and link.to_task.name in ng.get_task_names()
            ):
                ng.append_task(self.tasks[link.from_task.name].copy(graph=ng))
            if (
                link.from_task.name in ng.get_task_names()
                and link.to_task.name in ng.get_task_names()
            ):
                ng.add_link(
                    ng.tasks[link.from_task.name].outputs[link.from_socket._name],
                    ng.tasks[link.to_task.name].inputs[link.to_socket._name],
                )
        return ng

    def __getitem__(self, key: Union[str, List[str]]) -> "Graph":
        """Gets a sub-graph by the name(s) of tasks.

        Args:
            key (Union[str, List[str]]): The name(s) of the task(s).

        Returns:
            Graph: The sub-graph.
        """
        if isinstance(key, str):
            keys = [key]
        elif isinstance(key, list):
            keys = key
        else:
            raise TypeError("Key must be a string or list of strings.")
        ng = self.copy_subset(keys)
        return ng

    def __iadd__(self, other: "Graph") -> "Graph":
        """Adds another task graph to this task graph.

        Args:
            other (Graph): The other task graph to add.

        Returns:
            Graph: The combined task graph.
        """
        tasks = other.tasks._copy(graph=self)
        for task in tasks:
            # skip built-in tasks
            if task.name not in BUILTIN_TASKS:
                self.tasks._append(task)
        for link in other.links:
            self.add_link(
                self.tasks[link.from_task.name].outputs[link.from_socket._name],
                self.tasks[link.to_task.name].inputs[link.to_socket._name],
            )
        return self

    def __add__(self, other: "Graph") -> "Graph":
        """Returns a new task graph that is the combination of this and another.

        Args:
            other (Graph): The other task graph to add.

        Returns:
            Graph: The combined task graph.
        """
        new_graph = self.copy()
        new_graph += other
        return new_graph

    def delete_tasks(self, task_list: str | List[str]) -> None:
        """Deletes tasks from the task graph.

        Args:
            task_list (List[str]): The names of the tasks to delete.
        """
        if isinstance(task_list, str):
            task_list = [task_list]
        for name in task_list:
            if name not in self.get_task_names():
                raise ValueError(f"Task '{name}' not found in the task graph.")
            link_indices: List[int] = []
            for index, link in enumerate(self.links):
                if link.from_task.name == name or link.to_task.name == name:
                    link_indices.append(index)
            # Delete links in reverse order to avoid index shift
            for index in sorted(link_indices, reverse=True):
                del self.links[index]
            del self.tasks[name]

    def to_widget_value(self) -> dict:
        from aiida.node_graph.utils import gaph_to_short_json

        ngdata = gaph_to_short_json(self.to_dict(include_sockets=True))
        ngdata["nodes"] = ngdata.pop("tasks")
        for link in ngdata["links"]:
            link["from_node"] = link.pop("from_task")
            link["to_node"] = link.pop("to_task")
            link["from_socket"] = link.pop("from_socket")
            link["to_socket"] = link.pop("to_socket")
        return ngdata

    def __repr__(self) -> str:
        return f'Graph(name="{self.name}", uuid="{self.uuid}")'

    def __enter__(self):
        from aiida.node_graph.manager import active_graph as _active_graph

        self.___ctx = _active_graph(self)
        self.___ctx.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return self.___ctx.__exit__(exc_type, exc, tb)

    def run(self) -> None:
        """Runs the task graph."""
        from aiida.node_graph.engine.local import LocalEngine

        self.engine = LocalEngine()
        return self.engine.run(self)
