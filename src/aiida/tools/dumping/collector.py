# Note: I need access to a few attributes of the `ProfileDumper`/`GroupDumper`

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar, Dict, Optional, Type

from aiida import orm
from aiida.tools.dumping.config import NodeCollectorConfig

# from typing import TYPE_CHECKING
from aiida.tools.dumping.logger import DumpLogger


@dataclass
class NodeContainer:
    """Container for different types of nodes."""

    calculations: list['orm.CalculationNode'] = field(default_factory=list)
    workflows: list['orm.WorkflowNode'] = field(default_factory=list)
    data: list['orm.Data'] = field(default_factory=list)

    # Mapping between node types and container attribute names
    TYPE_MAP: ClassVar[Dict[Type, str]] = {
        'orm.CalculationNode': 'calculations',
        'orm.WorkflowNode': 'workflows',
        'orm.Data': 'data',
    }

    @property
    def dump_processes(self) -> bool:
        """Check if there are any processes to dump."""
        return len(self.calculations) > 0 or len(self.workflows) > 0

    @property
    def dump_data(self) -> bool:
        """Check if there are any data nodes to dump."""
        return len(self.data) > 0

    def __len__(self) -> int:
        """Get the total number of nodes."""
        return len(self.calculations) + len(self.workflows) + len(self.data)

    def num_processes(self) -> int:
        """Get the number of process nodes (calculations and workflows)."""
        return len(self.calculations) + len(self.workflows)

    def add_nodes(self, node_type: Type, nodes: list) -> None:
        """Add nodes of a specific type to the appropriate container."""
        type_name = node_type.__name__
        for key, attr in self.TYPE_MAP.items():
            if key.endswith(type_name):
                setattr(self, attr, nodes)
                break

    def is_empty(self) -> bool:
        """Check if the container is empty."""
        return len(self) == 0


class NodeDumpCollector:
    """Collects nodes based on specified criteria."""

    def __init__(
        self,
        incremental: bool,
        dump_logger: DumpLogger,
        config: NodeCollectorConfig,
        last_dump_time: datetime | None = None,
        group: Optional['orm.Group'] = None,
        # NOTE: This should be part of the DumpLogger, not extra
    ):
        """Initialize the collector with query parameters."""
        self.incremental = incremental
        self.last_dump_time = last_dump_time
        self.dump_logger = dump_logger
        self.group = group

        self.include_processes = config.include_processes
        self.include_data = config.include_data
        self.filter_by_last_dump_time = config.filter_by_last_dump_time
        self.only_top_level_calcs = config.only_top_level_calcs
        self.only_top_level_workflows = config.only_top_level_workflows

        self.orm_types = {'calculations': orm.CalculationNode, 'workflows': orm.WorkflowNode, 'data': orm.Data}

    def _resolve_filters(self, orm_type: Type) -> Dict[str, Any]:
        """
        Resolve filters for a query based on the collector's parameters.

        Args:
            orm_type: The ORM type class

        Returns:
            A dictionary of filters to apply to the query
        """
        filters = {}

        # Get the container attribute name for this orm type
        orm_key = self._get_orm_key(orm_type)

        # Filter by modification time if requested
        if self.filter_by_last_dump_time and self.last_dump_time:
            filters['mtime'] = {'>=': self.last_dump_time}

        # Filter out already dumped nodes if in incremental mode
        if self.incremental and self.dump_logger and hasattr(self.dump_logger, orm_key):
            node_list = getattr(self.dump_logger, orm_key)
            if node_list and len(node_list) > 0:
                filters['uuid'] = {'!in': node_list}

        return filters

    def _get_orm_key(self, orm_type: Type) -> str:
        """Get the container attribute name for an ORM type."""
        for attr, cls in self.orm_types.items():
            if cls == orm_type:
                return attr
        raise ValueError(f'Unknown ORM type: {orm_type}')

    def collect(self) -> NodeContainer:
        """
        Collect all node types using the collector's parameters.

        Returns:
            A NodeContainer with all requested nodes
        """
        container = NodeContainer()

        if self.include_processes:
            setattr(container, 'workflows', self.get_workflows())
            setattr(container, 'calculations', self.get_calculations())

        if self.include_data:
            msg = 'Mirroring of data nodes not yet implemented.'
            raise NotImplementedError(msg)

            # data_nodes = self._get_nodes(orm.Dat)
            # setattr(container, 'data', data_nodes)

        return container

    def _get_nodes(self, orm_type: Type) -> list:
        """
        Get nodes of a specific type with the collector's parameters.

        Args:
            orm_type: The ORM type to query

        Returns:
            A list of matching nodes
        """
        qb = orm.QueryBuilder()

        # Resolve filters for this query
        filters = self._resolve_filters(orm_type)

        # First append the node type with its filters
        qb.append(orm_type, filters=filters, tag='node')

        # If a group is provided, add the relationship to the query
        if self.group is not None:
            qb.append(orm.Group, filters={'id': self.group.id}, with_node='node')

        # If only_not_in_any_group is True, modify the query accordingly
        # if self.only_not_in_any_group:
        #     # Proper implementation for nodes not in any group
        #     qb.append(orm.Group, with_node='node', outerjoin=True)
        #     qb.add_filter(orm.Group, {'id': None})

        return qb.all(flat=True)

    # def _get_processes_to_dump(self) -> NodeContainer:
    #     """Retrieve the processeses from the collection nodes.

    #     Depending on the attributes of the ``CollectionDumper``, this method takes care of only selecting top-level
    #     workflows and calculations if they are not part of a workflow. This requires to use the actual ORM entities,
    #     rather than UUIDs, as the ``.caller``s have to be checked. In addition, sub-calculations

    #     :return: Instance of a ``ProcessesToDumpContainer``, that holds the selected calculations and workflows.
    #     """

    #     # ipdb.set_trace()
    #     if not self.group_nodes:
    #         return NodeContainer(calculations=[], workflows=[])

    #     # Better than: `nodes = [orm.load_node(n) for n in self.collection_nodes]`
    #     # As the list comprehension fetches each node from the DB individually
    #     nodes_orm = orm.QueryBuilder().append(orm.Node, filters={'uuid': {'in': self.group_nodes}}).all(flat=True)

    #     if self.group_dump_config.only_top_level_workflows:
    #         workflows = [node for node in nodes_orm if isinstance(node, orm.WorkflowNode) and node.caller is None]
    #     else:
    #         workflows = [node for node in nodes_orm if isinstance(node, orm.WorkflowNode)]

    #     if self.group_dump_config.only_top_level_calcs:

    #     # Use this small helper class rather than returning a dictionary for access via dot-notation
    #     return NodeContainer(
    #         calculations=calculations,
    #         workflows=workflows,
    #     )

    def get_calculations(self) -> list:
        """Get calculation nodes with the collector's parameters."""
        calculations = self._get_nodes(orm_type=self.orm_types['calculations'])

        if self.only_top_level_calcs:
            calculations = [node for node in calculations if node.caller is None]

        else:
            # Get sub-calculations that were called by workflows but which might themselves not be directly contained in
            # the collection
            called_calculations = []
            for workflow in self.workflows:
                called_calculations += [
                    node for node in workflow.called_descendants if isinstance(node, orm.CalculationNode)
                ]

            # Convert to set to avoid duplicates
            calculations = list(set(calculations + called_calculations))

        return calculations

    def get_workflows(self) -> list:
        """Get workflow nodes with the collector's parameters."""
        return self._get_nodes(orm_type=self.orm_types['workflows'])

    def get_data(self) -> list:
        """Get data nodes with the collector's parameters."""
        return self._get_nodes(orm_type=self.orm_types['data'])


# # Example usage:
# def example_usage():
#     # Create collector with parameters
#     collector = NodeCollector(
#         incremental=True,
#         filter_by_last_dump_time=True,
#         last_dump_time='2023-01-01'
#     )

#     # Get individual node lists
#     calculations = collector.get_calculations()

#     # Or get everything at once
#     container = collector.collect()

#     # Use the container
#     print(f"Found {len(container)} nodes:")
#     print(f"  - {len(container.calculations)} calculations")
#     print(f"  - {len(container.workflows)} workflows")
#     print(f"  - {len(container.data)} data nodes")

#     # Backward compatibility
#     container = NodeCollector.create_node_container(incremental=True)
