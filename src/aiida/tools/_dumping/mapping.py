###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""GroupNodeMapping to handle group-node relationships during dumping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Union, cast

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools._dumping.utils import GroupChanges, GroupInfo, GroupModificationInfo, NodeMembershipChange

LOGGER = AIIDA_LOGGER.getChild('tools._dumping.mapping')


@dataclass
class GroupNodeMapping:
    """Stores the mapping between groups and their member nodes."""

    # Map of group UUID to set of node UUIDs
    group_to_nodes: Dict[str, Set[str]] = field(default_factory=dict)

    # Map of node UUID to set of group UUIDs (for faster lookups)
    node_to_groups: Dict[str, Set[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to serializable dictionary."""
        return {
            'group_to_nodes': {group_uuid: list(node_uuids) for group_uuid, node_uuids in self.group_to_nodes.items()},
            'node_to_groups': {node_uuid: list(group_uuids) for node_uuid, group_uuids in self.node_to_groups.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GroupNodeMapping':
        """Create from serialized dictionary.

        :param data: Dictionary representation of the mapping
        """
        mapping = cls()

        # Load group_to_nodes mapping if present
        if 'group_to_nodes' in data and isinstance(data['group_to_nodes'], dict):
            for group_uuid, node_uuids in data['group_to_nodes'].items():
                for node_uuid in node_uuids:
                    # Just add to the group_to_nodes mapping, we'll rebuild node_to_groups after
                    if group_uuid not in mapping.group_to_nodes:
                        mapping.group_to_nodes[group_uuid] = set()
                    mapping.group_to_nodes[group_uuid].add(node_uuid)

        # Load node_to_groups mapping if present (or rebuild it)
        if 'node_to_groups' in data and isinstance(data['node_to_groups'], dict):
            for node_uuid, group_uuids in data['node_to_groups'].items():
                for group_uuid in group_uuids:
                    if node_uuid not in mapping.node_to_groups:
                        mapping.node_to_groups[node_uuid] = set()
                    mapping.node_to_groups[node_uuid].add(group_uuid)
        else:
            # If node_to_groups is missing, rebuild it from group_to_nodes
            for group_uuid, node_uuids in mapping.group_to_nodes.items():
                for node_uuid in node_uuids:
                    if node_uuid not in mapping.node_to_groups:
                        mapping.node_to_groups[node_uuid] = set()
                    mapping.node_to_groups[node_uuid].add(group_uuid)

        return mapping

    @classmethod
    def build_from_db(cls, groups: Optional[Union[List[orm.Group], List[str], List[int]]] = None) -> 'GroupNodeMapping':
        """Build a mapping from the current database state.

        :param groups: If provided, only build mapping for these specific groups.
            If None, build mapping for all groups.
        :return: Populated ``GroupNodeMapping`` instance
        """

        mapping = cls()

        # Query all groups and their nodes, or just the specific groups
        qb = orm.QueryBuilder()

        if groups is not None:
            # Only query the specified groups
            if all(isinstance(g, orm.Group) for g in groups):
                orm_groups = cast(List[orm.Group], groups)
                group_uuids = [g.uuid for g in orm_groups]
            else:
                group_uuids = [orm.load_group(g).uuid for g in groups]
            qb.append(orm.Group, tag='group', project=['uuid'], filters={'uuid': {'in': group_uuids}})
            LOGGER.report(f'Querying node memberships for {len(group_uuids)} groups...')
        else:
            # Query all groups
            qb.append(orm.Group, tag='group', project=['uuid'])
            LOGGER.report('Querying node memberships for all groups in profile...')

        qb.append(orm.Node, with_group='group', project=['uuid'])

        LOGGER.report('Retrieving group-node relationships from database...')
        results = qb.all()
        LOGGER.report(f'Processing {len(results)} group-node relationships...')

        for group_uuid, node_uuid in results:
            mapping._add_node_to_group(group_uuid, node_uuid)

        LOGGER.report('Completed group-node mapping.')
        return mapping

    def diff(self, other: 'GroupNodeMapping') -> GroupChanges:
        """Calculate differences between this mapping and another.

        :param other: Other ``GroupNodeMapping`` instance to compare to
        :return: Populated ``GroupChanges`` object
        """
        deleted_groups_info: List[GroupInfo] = []
        new_groups_info: List[GroupInfo] = []
        modified_groups_info: List[GroupModificationInfo] = []
        node_membership_changes: Dict[str, NodeMembershipChange] = {}

        self_group_uuids = set(self.group_to_nodes.keys())
        other_group_uuids = set(other.group_to_nodes.keys())

        # Deleted groups
        for group_uuid in self_group_uuids - other_group_uuids:
            deleted_groups_info.append(
                GroupInfo(
                    uuid=group_uuid,
                    node_count=len(self.group_to_nodes.get(group_uuid, set())),
                    # as group deleted, cannot be loaded from DB, so no label can be set via
                    # label=orm.load_group(group_uuid).label
                )
            )

        # New groups
        for group_uuid in other_group_uuids - self_group_uuids:
            new_groups_info.append(
                GroupInfo(
                    uuid=group_uuid,
                    node_count=len(other.group_to_nodes.get(group_uuid, set())),
                    label=orm.load_group(group_uuid).label,
                )
            )

        # Modified groups
        for group_uuid in self_group_uuids & other_group_uuids:
            self_nodes = self.group_to_nodes.get(group_uuid, set())
            other_nodes = other.group_to_nodes.get(group_uuid, set())

            added_nodes = list(other_nodes - self_nodes)
            removed_nodes = list(self_nodes - other_nodes)

            if added_nodes or removed_nodes:
                modified_groups_info.append(
                    GroupModificationInfo(
                        uuid=group_uuid,
                        label=orm.load_group(group_uuid).label,
                        nodes_added=added_nodes,
                        nodes_removed=removed_nodes,
                    )
                )

                # Track detailed node membership changes
                for node_uuid in added_nodes:
                    if node_uuid not in node_membership_changes:
                        node_membership_changes[node_uuid] = NodeMembershipChange()
                    node_membership_changes[node_uuid].added_to.append(group_uuid)

                for node_uuid in removed_nodes:
                    if node_uuid not in node_membership_changes:
                        node_membership_changes[node_uuid] = NodeMembershipChange()
                    node_membership_changes[node_uuid].removed_from.append(group_uuid)

        # Construct and return the GroupChangeInfo object
        group_changes = GroupChanges(
            deleted=deleted_groups_info,
            new=new_groups_info,
            modified=modified_groups_info,
            node_membership=node_membership_changes,
        )

        return group_changes

    def _add_node_to_group(self, group_uuid: str, node_uuid: str) -> None:
        """Add a node to a group in the mapping.

        :param group_uuid: The group to add to
        :param node_uuid: The node to be added
        """

        # Add to group->nodes mapping
        if group_uuid not in self.group_to_nodes:
            self.group_to_nodes[group_uuid] = set()
        self.group_to_nodes[group_uuid].add(node_uuid)

        # Add to node->groups mapping
        if node_uuid not in self.node_to_groups:
            self.node_to_groups[node_uuid] = set()
        self.node_to_groups[node_uuid].add(group_uuid)

    def _remove_node_from_group(self, group_uuid: str, node_uuid: str) -> None:
        """Remove a node from a group in the mapping.

        :param group_uuid: The group from which the node should be removed
        :param node_uuid: The node to be removed
        """

        # Remove from group->nodes mapping
        if group_uuid in self.group_to_nodes and node_uuid in self.group_to_nodes[group_uuid]:
            self.group_to_nodes[group_uuid].remove(node_uuid)
            # Clean up empty entries
            if not self.group_to_nodes[group_uuid]:
                del self.group_to_nodes[group_uuid]

        # Remove from node->groups mapping
        if node_uuid in self.node_to_groups and group_uuid in self.node_to_groups[node_uuid]:
            self.node_to_groups[node_uuid].remove(group_uuid)
            # Clean up empty entries
            if not self.node_to_groups[node_uuid]:
                del self.node_to_groups[node_uuid]

    def _remove_group(self, group_uuid: str) -> None:
        """Remove a group and all its node associations.

        :param group_uuid: The node to be removed
        """
        if group_uuid not in self.group_to_nodes:
            return

        # Get all nodes in this group
        nodes = self.group_to_nodes[group_uuid].copy()

        # Remove group from each node's groups
        for node_uuid in nodes:
            if node_uuid in self.node_to_groups:
                if group_uuid in self.node_to_groups[node_uuid]:
                    self.node_to_groups[node_uuid].remove(group_uuid)
                # Clean up empty entries
                if not self.node_to_groups[node_uuid]:
                    del self.node_to_groups[node_uuid]

        # Remove the group entry
        del self.group_to_nodes[group_uuid]
