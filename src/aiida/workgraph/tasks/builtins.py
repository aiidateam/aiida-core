from __future__ import annotations
from typing import Any, Dict, cast
from aiida.workgraph.task import Task
from aiida.workgraph import task, namespace, meta, dynamic
from aiida.node_graph.tasks.builtins import _GraphIOSharedMixin
from aiida.node_graph.task import ChildTaskSet
from aiida.node_graph.socket import BaseSocket
from aiida.node_graph import RuntimeExecutor
from aiida import orm
from aiida.node_graph.task_spec import TaskSpec
from aiida.node_graph.socket_spec import SocketSpec, SocketMeta
from typing import Annotated
from aiida.workgraph.executors.builtins import update_ctx, get_context, select, return_input
from aiida.node_graph.task import BuiltinPolicy
from aiida.workgraph.executors.builtins import load_node, load_code


class GraphLevelTask(_GraphIOSharedMixin, Task):  # type: ignore[misc]  # node_graph ships no type information
    """Graph level task variant with shared IO."""

    _default_spec = TaskSpec(
        identifier='workgraph.graph_level_task',
        catalog='Builtins',
        base_class_path='aiida.workgraph.tasks.builtins.GraphLevelTask',
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._unify_io()


class Zone(Task):
    """
    Extend the Task class to include a 'children' attribute.
    """

    _default_spec = TaskSpec(
        identifier='workgraph.zone',
        task_type='ZONE',
        catalog='Control',
        inputs=namespace(),
        outputs=namespace(),
        base_class_path='aiida.workgraph.tasks.builtins.Zone',
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.children = ChildTaskSet(parent=self)

    def add_task(self, *args: Any, **kwargs: Any) -> Task:
        """Syntactic sugar to add a task to the zone."""
        task = self.graph.add_task(*args, **kwargs)
        self.children.add(task)
        task.parent = self
        return cast(Task, task)

    def to_dict(self, include_sockets: bool = False, should_serialize: bool = False) -> Dict[str, Any]:
        tdata = super().to_dict(include_sockets=include_sockets, should_serialize=should_serialize)
        tdata['children'] = [task.name for task in self.children]
        return tdata


class While(Zone):
    """While"""

    _default_spec = TaskSpec(
        identifier='workgraph.while_zone',
        task_type='WHILE',
        catalog='Control',
        inputs=namespace(
            max_iterations=Annotated[int, SocketSpec('workgraph.any', default=10000)],
            conditions=Annotated[Any, SocketSpec('workgraph.any', link_limit=100000)],
        ),
        base_class_path='aiida.workgraph.tasks.builtins.While',
    )


class If(Zone):
    """If task"""

    _default_spec = TaskSpec(
        identifier='workgraph.if_zone',
        task_type='IF',
        catalog='Control',
        inputs=namespace(
            invert_condition=Annotated[bool, SocketSpec('workgraph.bool', default=False)],
            conditions=Annotated[Any, SocketSpec('workgraph.any', link_limit=100000)],
        ),
        base_class_path='aiida.workgraph.tasks.builtins.If',
    )


class Map(Zone):
    """Run a set of tasks once per entry of a dynamic-namespace (dict) source.

    A Map iterates keyed entries, not a bare sequence. While building the body,
    ``value`` and ``key`` are placeholders for the current entry; the engine
    clones the body once per entry and binds them.
    """

    _default_spec = TaskSpec(
        identifier='workgraph.map_zone',
        task_type='MAP',
        catalog='Control',
        inputs=namespace(
            source=dynamic(Any),
        ),
        outputs=namespace(),
        base_class_path='aiida.workgraph.tasks.builtins.Map',
    )

    def _map_item_task(self) -> Task:
        """Return the single ``map_item`` child, creating it on first access."""
        for child in self.children:
            if child.identifier == 'workgraph.map_item':
                return cast(Task, child)
        return self.add_task('workgraph.map_item')

    @property
    def value(self) -> BaseSocket:
        """Placeholder for the current entry's value while iterating the source."""
        return self._map_item_task().outputs.value

    @property
    def key(self) -> BaseSocket:
        """Placeholder for the current entry's key while iterating the source."""
        return self._map_item_task().outputs.key

    @property
    def gather_item_task(self) -> Task:
        for child in self.children:
            if child.identifier == 'workgraph.gather_item':
                return cast(Task, child)
        return self.add_task('workgraph.gather_item')

    def _contains_task(self, target: Task) -> bool:
        """True if ``target`` is a descendant of this zone (recursing nested zones)."""
        stack = list(self.children)
        while stack:
            task = stack.pop()
            if task.name == target.name:
                return True
            stack.extend(getattr(task, 'children', []))
        return False

    def gather(self, sockets: Dict[str, BaseSocket]) -> BaseSocket:
        """Collect per-entry results into the zone outputs, one namespace per name."""
        # Validate every source before mutating anything (the loop below and even
        # `self.gather_item_task` add state), so a rejection leaves the zone
        # unchanged and rebuildable.
        for name, socket in sockets.items():
            source = socket._task
            if not self._contains_task(source):
                msg = (
                    f"Map.gather() source '{name}' ('{source.name}') is outside the Map zone (one value, not "
                    f'per-iteration). Move a per-iteration task inside the zone, or use a shared value (graph input) directly.'
                )
                raise ValueError(msg)
        gather_item = self.gather_item_task
        for name in sockets:
            gather_item.add_input_spec('workgraph.any', name=name)
            self.add_output_spec('workgraph.namespace', name=name)
        gather_item.set_inputs(sockets)
        return gather_item.outputs


class MapItem(Task):
    """MapItem"""

    # turn off framework builtins for these graph-level nodes
    _BUILTINS_POLICY = BuiltinPolicy(input_wait=False, output_wait=False, default_output=False)

    _default_spec = TaskSpec(
        identifier='workgraph.map_item',
        task_type='Normal',
        catalog='Control',
        inputs=namespace(
            source=SocketSpec('workgraph.any', link_limit=100000, meta=SocketMeta(required=False)),
            key=SocketSpec('workgraph.string', meta=SocketMeta(required=False)),
        ),
        outputs=namespace(key=str, value=Any),
        base_class_path='aiida.workgraph.tasks.builtins.MapItem',
    )


class GatherItem(Task):
    """GatherItem"""

    # turn off framework builtins for these graph-level nodes
    _BUILTINS_POLICY = BuiltinPolicy(input_wait=True, output_wait=False, default_output=False)

    _default_spec = TaskSpec(
        identifier='workgraph.gather_item',
        task_type='Normal',
        catalog='Control',
        inputs=namespace(),
        outputs=namespace(),
        executor=RuntimeExecutor.from_callable(return_input),
        base_class_path='aiida.workgraph.tasks.builtins.GatherItem',
    )


class SetContext(Task):
    """SetContext"""

    _default_spec = TaskSpec(
        identifier='workgraph.set_context',
        task_type='Normal',
        catalog='Control',
        inputs=namespace(
            context=SocketSpec('workgraph.any', meta=SocketMeta(required=False)),
            key=Any,
            value=Any,
        ),
        executor=RuntimeExecutor.from_callable(update_ctx),
        base_class_path='aiida.workgraph.tasks.builtins.SetContext',
    )


class GetContext(Task):
    """GetContext"""

    _default_spec = TaskSpec(
        identifier='workgraph.get_context',
        task_type='Normal',
        catalog='Control',
        inputs=namespace(
            context=SocketSpec('workgraph.any', meta=SocketMeta(required=False)),
            key=Any,
        ),
        outputs=namespace(result=Any),
        executor=RuntimeExecutor.from_callable(get_context),
        base_class_path='aiida.workgraph.tasks.builtins.GetContext',
    )


class Select(Task):
    """Select"""

    _default_spec = TaskSpec(
        identifier='workgraph.select',
        task_type='Normal',
        catalog='Control',
        inputs=namespace(
            condition=Any,
            true=Any,
            false=Any,
        ),
        outputs=namespace(result=Any),
        executor=RuntimeExecutor.from_callable(select),
        base_class_path='aiida.workgraph.tasks.builtins.Select',
    )


# The ``@task`` decorator and aiida-core's ``orm`` constructors carry no type
# information yet, so these thin wrappers need explicit ignores. Drop them once
# ``aiida_workgraph.decorator`` and aiida-core are annotated.
@task(identifier='workgraph.aiida_int')  # type: ignore[untyped-decorator]
def aiida_int(value: int) -> orm.Int:
    return orm.Int(value)  # type: ignore[no-untyped-call]


@task(identifier='workgraph.aiida_float')  # type: ignore[untyped-decorator]
def aiida_float(value: float) -> orm.Float:
    return orm.Float(value)  # type: ignore[no-untyped-call]


@task(identifier='workgraph.aiida_string')  # type: ignore[untyped-decorator]
def aiida_string(value: str) -> orm.Str:
    return orm.Str(value)  # type: ignore[no-untyped-call]


@task(identifier='workgraph.aiida_list')  # type: ignore[untyped-decorator]
def aiida_list(value: list[Any]) -> orm.List:
    return orm.List(value)  # type: ignore[no-untyped-call]


@task(identifier='workgraph.aiida_dict')  # type: ignore[untyped-decorator]
def aiida_dict(value: dict[str, Any]) -> orm.Dict:
    return orm.Dict(value)  # type: ignore[no-untyped-call]


class AiiDANode(Task):
    """AiiDANode"""

    identifier = 'workgraph.load_node'
    name = 'AiiDANode'
    catalog = 'Test'

    _default_spec = TaskSpec(
        identifier=identifier,
        task_type='Normal',
        inputs=namespace(
            pk=Annotated[int, meta(required=False)],
            uuid=Annotated[str, meta(required=False)],
        ),
        outputs=namespace(node=orm.Node),
        executor=RuntimeExecutor.from_callable(load_node),
        base_class_path='aiida.workgraph.task.Task',
    )


class AiiDACode(Task):
    """AiiDACode"""

    identifier = 'workgraph.load_code'
    name = 'AiiDACode'
    catalog = 'Test'

    _default_spec = TaskSpec(
        identifier=identifier,
        task_type='Normal',
        inputs=namespace(
            pk=Annotated[int, meta(required=False)],
            uuid=Annotated[str, meta(required=False)],
            label=Annotated[str, meta(required=False)],
        ),
        outputs=namespace(code=orm.Code),
        executor=RuntimeExecutor.from_callable(load_code),
        base_class_path='aiida.workgraph.task.Task',
    )
