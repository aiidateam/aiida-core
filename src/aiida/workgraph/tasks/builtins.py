from __future__ import annotations

from typing import Annotated, Any

from node_graph import RuntimeExecutor
from node_graph.socket import BaseSocket
from node_graph.socket_spec import SocketMeta, SocketSpec
from node_graph.task import BuiltinPolicy, ChildTaskSet
from node_graph.task_spec import TaskSpec
from node_graph.tasks.builtins import _GraphIOSharedMixin

from aiida import orm
from aiida.workgraph import dynamic, meta, namespace, task
from aiida.workgraph.executors.builtins import get_context, load_code, load_node, return_input, select, update_ctx
from aiida.workgraph.task import Task


class GraphLevelTask(_GraphIOSharedMixin, Task):
    """Graph level task variant with shared IO."""

    _default_spec = TaskSpec(
        identifier='workgraph.graph_level_task',
        catalog='Builtins',
        base_class_path='aiida.workgraph.tasks.builtins.GraphLevelTask',
    )

    def __init__(self, *args, **kwargs):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.children = ChildTaskSet(parent=self)

    def add_task(self, *args, **kwargs) -> Task:
        """Syntactic sugar to add a task to the zone."""
        task = self.graph.add_task(*args, **kwargs)
        self.children.add(task)
        task.parent = self
        return task

    def to_dict(self, **kwargs) -> dict[str, Any]:
        tdata = super().to_dict(**kwargs)
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
    """Map"""

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def item(self):
        for child in self.children:
            if child.identifier == 'workgraph.map_item':
                return child.outputs
        # create a child map_item_task if it does not exist
        map_item_task = self.add_task('workgraph.map_item')
        return map_item_task.outputs

    @property
    def gather_item_task(self) -> Task | None:
        for child in self.children:
            if child.identifier == 'workgraph.gather_item':
                return child
        gather_item = self.add_task('workgraph.gather_item')
        return gather_item

    def gather(self, sockets: dict[str, BaseSocket]) -> None:
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


@task(identifier='workgraph.aiida_int')
def aiida_int(value: int) -> orm.Int:
    return orm.Int(value)


@task(identifier='workgraph.aiida_float')
def aiida_float(value: float) -> orm.Float:
    return orm.Float(value)


@task(identifier='workgraph.aiida_string')
def aiida_string(value: str) -> orm.Str:
    return orm.Str(value)


@task(identifier='workgraph.aiida_list')
def aiida_list(value: list) -> orm.List:
    return orm.List(value)


@task(identifier='workgraph.aiida_dict')
def aiida_dict(value: dict) -> orm.Dict:
    return orm.Dict(value)


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
