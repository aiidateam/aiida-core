from collections.abc import Callable

from node_graph.property import TaskProperty as BaseTaskProperty


class TaskProperty(BaseTaskProperty):
    """Represent a property of a Task in the AiiDA WorkGraph."""

    def validate(self, value: any) -> None:
        super().validate(value)

    @classmethod
    def new(cls, identifier: Callable | str, name: str | None = None, **kwargs) -> 'TaskProperty':
        """Create a property from a identifier."""
        # use PropertyPool from aiida.workgraph.properties
        # to override the default PropertyPool from node_graph
        from aiida.workgraph.properties import PropertyPool

        return super().new(identifier, name=name, PropertyPool=PropertyPool, **kwargs)


def unwrap_aiida_node(value):
    if hasattr(value, 'value'):
        return value.value
    return TaskProperty.NOT_ADAPTED


TaskProperty.register_validation_adapter(unwrap_aiida_node)
