###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Class to collect nodes for mirror feature."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar, Dict, Type

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.mirror.config import NodeCollectorConfig, NodeMirrorGroupScope
from aiida.tools.mirror.logger import MirrorLogger

logger = AIIDA_LOGGER.getChild('tools.mirror.collector')


@dataclass
class MirrorNodeContainer:
    calculations: list['orm.CalculationNode'] = field(default_factory=list)
    workflows: list['orm.WorkflowNode'] = field(default_factory=list)
    data: list['orm.Data'] = field(default_factory=list)

    # Mapping between node types and container attribute names
    TYPE_MAP: ClassVar[Dict[str, str]] = {
        'orm.CalculationNode': 'calculations',
        'orm.WorkflowNode': 'workflows',
        'orm.Data': 'data',
    }

    @property
    def should_mirror_processes(self) -> bool:
        return len(self.calculations) > 0 or len(self.workflows) > 0

    @property
    def should_mirror_data(self) -> bool:
        return len(self.data) > 0

    def __len__(self) -> int:
        return len(self.calculations) + len(self.workflows) + len(self.data)

    def num_processes(self) -> int:
        return len(self.calculations) + len(self.workflows)

    def add_nodes(self, node_type: Type, nodes: list) -> None:
        type_name = node_type.__name__
        for key, attr in self.TYPE_MAP.items():
            if key.endswith(type_name):
                setattr(self, attr, nodes)
                break

    def is_empty(self) -> bool:
        return len(self) == 0


class MirrorNodeCollector:
    def __init__(
        self,
        mirror_logger: 'MirrorLogger',
        config: 'NodeCollectorConfig',
        last_mirror_time: datetime | None = None,
    ):
        self.last_mirror_time = last_mirror_time
        self.mirror_logger = mirror_logger
        self.config = config

        self.include_processes = config.include_processes
        self.include_data = config.include_data
        self.filter_by_last_mirror_time = config.filter_by_last_mirror_time
        self.only_top_level_calcs = config.only_top_level_calcs
        self.only_top_level_workflows = config.only_top_level_workflows

        self.orm_types = {
            'calculations': orm.CalculationNode,
            'workflows': orm.WorkflowNode,
            'data': orm.Data,
        }

    def collect(self, group: 'orm.Group' = None) -> MirrorNodeContainer:
        msg = 'Collecting nodes from the database. For the first mirror, this can take a while.'
        logger.report(msg)

        container = MirrorNodeContainer()

        if self.include_processes:
            # Get workflow nodes
            workflows = self._get_nodes('workflows', group=group, top_level_only=self.only_top_level_workflows)
            container.workflows = workflows

            # Get calculation nodes
            calculations = self._get_nodes('calculations', group=group, top_level_only=self.only_top_level_calcs)

            # If not using top-level-only filter, add descendant calculations from workflows
            if not self.only_top_level_calcs and workflows:
                descendant_calcs = self._get_workflow_descendants(workflows)
                # Combine and remove duplicates
                calculations = list(set(calculations + descendant_calcs))

            container.calculations = calculations

        if self.include_data:
            # Get data nodes
            try:
                data_nodes = self._get_nodes('data', group=group, scope=self.config.group_scope)
                container.data = data_nodes
            except NotImplementedError:
                # Keep the existing behavior
                msg = 'Mirroring of data nodes not yet implemented.'
                raise NotImplementedError(msg)

        return container

    def _resolve_filters(self, orm_key: str) -> Dict[str, Any]:
        filters = {}

        # Filter by modification time if requested
        if self.filter_by_last_mirror_time and self.last_mirror_time:
            filters['mtime'] = {'>=': self.last_mirror_time.astimezone()}

        # Filter out already logged nodes if mirror_logger is available
        if self.mirror_logger and hasattr(self.mirror_logger, orm_key):
            node_store = getattr(self.mirror_logger, orm_key)
            if node_store and len(node_store) > 0:
                filters['uuid'] = {'!in': list(node_store.entries.keys())}

        return filters

    def _get_nodes(self, orm_key: str, group: 'orm.Group' = None, top_level_only: bool = False) -> list['orm.Node']:
        orm_type = self.orm_types[orm_key]

        # Basic filters for the query
        filters = self._resolve_filters(orm_key)

        # Build query based on scope
        if self.config.group_scope == NodeMirrorGroupScope.IN_GROUP:
            if group is None:
                raise ValueError('Group must be provided when scope is IN_GROUP')
            nodes = self._query_group_nodes(orm_type, group, filters)

        elif self.config.group_scope == NodeMirrorGroupScope.ANY:
            nodes = self._query_all_nodes(orm_type, filters)

        elif self.config.group_scope == NodeMirrorGroupScope.NO_GROUP:
            nodes = self._query_no_group_nodes(orm_type, filters)

        else:
            raise ValueError('Unknown scope: ')

        # Apply top-level filtering if requested
        if top_level_only:
            nodes = [node for node in nodes if node.caller is None]

        return nodes

    def _query_group_nodes(self, orm_type: orm.Node, group: 'orm.Group', filters: Dict[str, Any]) -> list['orm.Node']:
        qb = orm.QueryBuilder()
        qb.append(orm.Group, filters={'id': group.id}, tag='group')
        qb.append(orm_type, filters=filters, with_group='group', tag='node')
        return qb.all(flat=True)

    def _query_all_nodes(self, orm_type: orm.Node, filters: Dict[str, Any]) -> list['orm.Node']:
        qb = orm.QueryBuilder()
        qb.append(orm_type, filters=filters, tag='node')
        return qb.all(flat=True)

    def _query_no_group_nodes(self, orm_type: orm.Node, filters: Dict[str, Any]) -> list['orm.Node']:
        # First get all nodes
        all_nodes = self._query_all_nodes(orm_type, filters)

        # Then get all nodes that are in groups
        qb = orm.QueryBuilder()
        qb.append(orm.Group, tag='group')
        qb.append(orm_type, with_group='group', tag='node')
        grouped_nodes = qb.all(flat=True)

        # Also include descendant nodes of process nodes
        descendant_nodes = []
        for node in grouped_nodes:
            if isinstance(node, orm.ProcessNode):
                descendant_nodes.extend(node.called_descendants)

        # Combine and convert to a set for efficient membership checking
        all_grouped_nodes = set(grouped_nodes + descendant_nodes)

        # Return only nodes that are not in any group
        return [node for node in all_nodes if node not in all_grouped_nodes]

    def _get_workflow_descendants(self, workflows: list['orm.WorkflowNode']) -> list[orm.Node]:
        descendants = []
        for workflow in workflows:
            for node in workflow.called_descendants:
                if isinstance(node, orm.CalculationNode):
                    descendants.append(node)
        return descendants


# @dataclass
# class NodeContainer:
#     """Container for different types of nodes."""

#     calculations: list['orm.CalculationNode'] = field(default_factory=list)
#     workflows: list['orm.WorkflowNode'] = field(default_factory=list)
#     data: list['orm.Data'] = field(default_factory=list)

#     # Mapping between node types and container attribute names
#     TYPE_MAP: ClassVar[Dict[Type, str]] = {
#         'orm.CalculationNode': 'calculations',
#         'orm.WorkflowNode': 'workflows',
#         'orm.Data': 'data',
#     }

#     @property
#     def mirror_processes(self) -> bool:
#         """Check if there are any processes to mirror."""
#         return len(self.calculations) > 0 or len(self.workflows) > 0

#     @property
#     def mirror_data(self) -> bool:
#         """Check if there are any data nodes to mirror."""
#         return len(self.data) > 0

#     def __len__(self) -> int:
#         """Get the total number of nodes."""
#         return len(self.calculations) + len(self.workflows) + len(self.data)

#     def num_processes(self) -> int:
#         """Get the number of process nodes (calculations and workflows)."""
#         return len(self.calculations) + len(self.workflows)

#     def add_nodes(self, node_type: Type, nodes: list) -> None:
#         """Add nodes of a specific type to the appropriate container."""
#         type_name = node_type.__name__
#         for key, attr in self.TYPE_MAP.items():
#             if key.endswith(type_name):
#                 setattr(self, attr, nodes)
#                 break

#     def is_empty(self) -> bool:
#         """Check if the container is empty."""
#         return len(self) == 0


# class NodeDumpCollector:
#     """Collects nodes based on specified criteria."""

#     def __init__(
#         self,
#         mirror_logger: MirrorLogger,
#         config: NodeCollectorConfig,
#         last_mirror_time: datetime | None = None,
#     ):
#         """Initialize the collector with query parameters."""
#         self.last_mirror_time = last_mirror_time
#         self.mirror_logger = mirror_logger

#         self.include_processes = config.include_processes
#         self.include_data = config.include_data
#         self.filter_by_last_mirror_time = config.filter_by_last_mirror_time
#         self.only_top_level_calcs = config.only_top_level_calcs
#         self.only_top_level_workflows = config.only_top_level_workflows

#         self.orm_types = {'calculations': orm.CalculationNode, 'workflows': orm.WorkflowNode, 'data': orm.Data}

#     def _resolve_filters(self, orm_type: Type) -> Dict[str, Any]:
#         """
#         Resolve filters for a query based on the collector's parameters.

#         Args:
#             orm_type: The ORM type class

#         Returns:
#             A dictionary of filters to apply to the query
#         """
#         filters = {}

#         # Get the container attribute name for this orm type
#         orm_key = self._get_orm_key(orm_type)

#         # Filter by modification time if requested
#         if self.filter_by_last_mirror_time and self.last_mirror_time:
#             filters['mtime'] = {'>=': self.last_mirror_time.astimezone()}

#         if self.mirror_logger and hasattr(self.mirror_logger, orm_key):
#             node_store = getattr(self.mirror_logger, orm_key)
#             if node_store and len(node_store) > 0:
#                 filters['uuid'] = {'!in': list(node_store.entries.keys())}

#         return filters

#     def _get_orm_key(self, orm_type: Type) -> str:
#         """Get the container attribute name for an ORM type."""
#         for attr, cls in self.orm_types.items():
#             if cls == orm_type:
#                 return attr
#         raise ValueError(f'Unknown ORM type: {orm_type}')

#     def collect(self, group) -> NodeContainer:
#         """
#         Collect all node types using the collector's parameters.

#         Returns:
#             A NodeContainer with all requested nodes
#         """
#         container = NodeContainer()

#         if self.include_processes:
#             container.workflows = self._get_group_workflows(group=group)
#             container.calculations = self.get_calculations(group=group)

#         if self.include_data:
#             msg = 'Mirroring of data nodes not yet implemented.'
#             raise NotImplementedError(msg)

#             # data_nodes = self._get_nodes(orm.Dat)
#             # setattr(container, 'data', data_nodes)

#         return container

#     def _get_group_nodes(self, orm_type: Type, group: orm.Group) -> list[orm.Node]:
#         """
#         """
#         qb = orm.QueryBuilder()

#         # Resolve filters for this query
#         filters = self._resolve_filters(orm_type)

#         qb.append(orm.Group, filters={'id': group.id}, tag='group')
#         qb.append(orm_type, filters=filters, with_group='group', tag='node')

#         return qb.all(flat=True)

#     def _get_profile_nodes(self, orm_type: Type) -> list[orm.Node]:
#         """
#         """
#         qb = orm.QueryBuilder()

#         # Resolve filters for this query
#         filters = self._resolve_filters(orm_type)

#         qb.append(orm_type, filters=filters, tag='node')

#         return qb.all(flat=True)

#     def _get_no_group_nodes(self, orm_type: Type):
#         """
#         """

#         import ipdb; ipdb.set_trace()
#         profile_groups = cast(list[orm.Group], orm.QueryBuilder().append(orm.Group).all(flat=True))

#         profile_nodes = self._get_profile_nodes(orm_type=orm_type)

#         nodes_in_groups: list[orm.Node] = [node for group in profile_groups for node in group.nodes]

#         # Need to expand here also with the called_descendants of `WorkflowNodes`, otherwise the called
#         # `CalculationNode`s for `WorkflowNode`s that are part of a group are mirrored twice
#         # Get the called descendants of WorkflowNodes within the nodes_in_groups list
#         sub_nodes_in_groups: list[orm.Node] = [
#             node
#             for n in nodes_in_groups
#             # if isinstance((workflow_node := orm.load_node(n)), orm.WorkflowNode)
#             if isinstance((workflow_node := n), orm.ProcessNode)
#             for node in workflow_node.called_descendants
#         ]

#         nodes_in_groups += sub_nodes_in_groups

#         no_group_nodes: list[orm.Node] = [
#             profile_node for profile_node in profile_nodes if profile_node not in nodes_in_groups
#         ]

#         return no_group_nodes

#     def _get_group_calculations(self, group: orm.Group | None = None) -> list:
#         """Get calculation nodes with the collector's parameters."""
#         calculations = self._get_group_nodes(orm_type=self.orm_types['calculations'], group=group)

#         if self.only_top_level_calcs:
#             calculations = [node for node in calculations if node.caller is None]

#         else:
#             # Get sub-calculations that were called by workflows but which might themselves not be directly contained
#             in
#             # the collection
#             called_calculations = []
#             for workflow in self.workflows:
#                 called_calculations += [
#                     node for node in workflow.called_descendants if isinstance(node, orm.CalculationNode)
#                 ]

#             # Convert to set to avoid duplicates
#             calculations = list(set(calculations + called_calculations))

#         return calculations

#     def _get_group_workflows(self, group: orm.Group | None = None) -> list:
#         """Get workflow nodes with the collector's parameters."""
#         return self._get_group_nodes(orm_type=self.orm_types['workflows'], group=group)

#     def _get_group_data(self, group: orm.Group | None = None) -> list:
#         """Get data nodes with the collector's parameters."""
#         return self._get_group_nodes(orm_type=self.orm_types['data'], group=group)


# # Example usage:
# def example_usage():
#     # Create collector with parameters
#     collector = NodeCollector(
#         incremental=True,
#         filter_by_last_mirror_time=True,
#         last_mirror_time='2023-01-01'
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


# def _get_processes_to_mirror(self) -> NodeContainer:
#     """Retrieve the processeses from the collection nodes.

#     Depending on the attributes of the ``CollectionDumper``, this method takes care of only selecting top-level
#     workflows and calculations if they are not part of a workflow. This requires to use the actual ORM entities,
#     rather than UUIDs, as the ``.caller``s have to be checked. In addition, sub-calculations

#     :return: Instance of a ``ProcessesToMirrorContainer``, that holds the selected calculations and workflows.
#     """

#     # ipdb.set_trace()
#     if not self.group_nodes:
#         return NodeContainer(calculations=[], workflows=[])

#     # Better than: `nodes = [orm.load_node(n) for n in self.collection_nodes]`
#     # As the list comprehension fetches each node from the DB individually
#     nodes_orm = orm.QueryBuilder().append(orm.Node, filters={'uuid': {'in': self.group_nodes}}).all(flat=True)

#     if self.group_mirror_config.only_top_level_workflows:
#         workflows = [node for node in nodes_orm if isinstance(node, orm.WorkflowNode) and node.caller is None]
#     else:
#         workflows = [node for node in nodes_orm if isinstance(node, orm.WorkflowNode)]

#     if self.group_mirror_config.only_top_level_calcs:

#     # Use this small helper class rather than returning a dictionary for access via dot-notation
#     return NodeContainer(
#         calculations=calculations,
#         workflows=workflows,
#     )
