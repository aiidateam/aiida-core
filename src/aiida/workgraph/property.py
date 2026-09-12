from typing import Union, Optional, Callable
from aiida.node_graph.property import TaskProperty as BaseTaskProperty


class TaskProperty(BaseTaskProperty):
    """Represent a property of a Task in the AiiDA WorkGraph."""

    def validate(self, value: any) -> None:
        super().validate(value)

    @classmethod
    def new(cls, identifier: Union[Callable, str], name: Optional[str] = None, **kwargs) -> 'TaskProperty':
        """Create a property from a identifier."""
        # use PropertyPool from aiida_workgraph.properties
        # to override the default PropertyPool from node_graph
        from aiida.workgraph.properties import PropertyPool

        return super().new(identifier, name=name, PropertyPool=PropertyPool, **kwargs)


def unwrap_aiida_node(value):
    if hasattr(value, 'value'):
        return value.value
    return TaskProperty.NOT_ADAPTED


TaskProperty.register_validation_adapter(unwrap_aiida_node)
