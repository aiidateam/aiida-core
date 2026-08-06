from node_graph.socket import (
    TaskSocket as BaseTaskSocket,
)
from node_graph.socket import (
    TaskSocketNamespace as BaseTaskSocketNamespace,
)

from aiida import orm
from aiida.workgraph.property import TaskProperty
from aiida.workgraph.registry import type_mapping


class TaskSocket(BaseTaskSocket):
    """Represent a socket of a Task in the AiiDA WorkGraph."""

    # use TaskProperty from aiida.workgraph.property
    # to override the default TaskProperty from node_graph
    _socket_property_class = TaskProperty

    @property
    def _decorator(self):
        from aiida.workgraph.decorator import task

        return task

    @property
    def node_value(self):
        return self.get_node_value()

    def get_node_value(self):
        """Obtain the actual Python `value` of the object attached to the Socket."""
        if isinstance(self.value, orm.Data):
            if hasattr(self.value, 'value'):
                return self.value.value
            else:
                raise ValueError(
                    'Data node does not have a value attribute. We do not know how to extract the raw Python value.'
                )
        else:
            return self.value


class TaskSocketNamespace(BaseTaskSocketNamespace):
    """Represent a namespace of a Task in the AiiDA WorkGraph."""

    _identifier = 'workgraph.namespace'
    _socket_property_class = TaskProperty
    _type_mapping: dict = type_mapping

    @property
    def _decorator(self):
        from aiida.workgraph.decorator import task

        return task

    def __init__(self, *args, **kwargs):
        super().__init__(*args, entry_point='aiida_workgraph.socket', **kwargs)
