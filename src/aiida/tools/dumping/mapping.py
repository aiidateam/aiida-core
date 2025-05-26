###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

"""GroupNodeMapping to handle group-node relationships."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set

from aiida import orm
from aiida.tools.dumping.utils import GroupChanges, GroupInfo, GroupModificationInfo, NodeMembershipChange


@dataclass
class GroupNodeMapping:
    """Stores the mapping between groups and their member nodes."""

    # Map of group UUID to set of node UUIDs
    group_to_nodes: Dict[str, Set[str]] = field(default_factory=dict)

    # Map of node UUID to set of group UUIDs (for faster lookups)
    node_to_groups: Dict[str, Set[str]] = field(default_factory=dict)

    def _add_node_to_group(self, group_uuid: str, node_uuid: str) -> None:
        """Add a node to a group in the mapping."""
        # Add to group->nodes mapping
        if group_uuid not in self.group_to_nodes:
            self.group_to_nodes[group_uuid] = set()
        self.group_to_nodes[group_uuid].add(node_uuid)

        # Add to node->groups mapping
        if node_uuid not in self.node_to_groups:
            self.node_to_groups[node_uuid] = set()
        self.node_to_groups[node_uuid].add(group_uuid)

    def _remove_node_from_group(self, group_uuid: str, node_uuid: str) -> None:
        """Remove a node from a group in the mapping."""
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
        """Remove a group and all its node associations."""
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

    def to_dict(self) -> Dict:
        """Convert to serializable dictionary."""
        return {
            'group_to_nodes': {group_uuid: list(node_uuids) for group_uuid, node_uuids in self.group_to_nodes.items()},
            'node_to_groups': {node_uuid: list(group_uuids) for node_uuid, group_uuids in self.node_to_groups.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GroupNodeMapping':
        """Create from serialized dictionary."""
        mapping = cls()

        # Handle old format (backward compatibility)
        if 'group_to_nodes' in data and isinstance(data['group_to_nodes'], dict):
            for group_uuid, node_uuids in data['group_to_nodes'].items():
                for node_uuid in node_uuids:
                    mapping._add_node_to_group(group_uuid, node_uuid)

        # Handle new format with both mappings
        elif isinstance(data, dict):
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
    def build_from_db(cls) -> 'GroupNodeMapping':
        """Build a mapping from the current database state."""
        mapping = cls()

        # Query all groups and their nodes
        qb = orm.QueryBuilder()
        qb.append(orm.Group, tag='group', project=['uuid'])
        qb.append(orm.Node, with_group='group', project=['uuid'])

        for group_uuid, node_uuid in qb.all():
            mapping._add_node_to_group(group_uuid, node_uuid)

        return mapping

    def diff(self, other: 'GroupNodeMapping') -> GroupChanges:
        """
        Calculate differences between this mapping and another.

        Returns:
            GroupChangeInfo object with detailed group changes.
        """
        # TODO: Seems like when nodes added to a group, this group is still presented as "new"
        deleted_groups_info = []
        new_groups_info = []
        modified_groups_info = []
        node_membership_changes = {}

        self_group_uuids = set(self.group_to_nodes.keys())
        other_group_uuids = set(other.group_to_nodes.keys())

        # Deleted groups
        for group_uuid in self_group_uuids - other_group_uuids:
            deleted_groups_info.append(
                GroupInfo(
                    uuid=group_uuid,
                    node_count=len(self.group_to_nodes.get(group_uuid, set())),
                    # as group deleted, cannot be loaded from DB
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
        return GroupChanges(
            deleted=deleted_groups_info,
            new=new_groups_info,
            modified=modified_groups_info,
            node_membership=node_membership_changes,
        )
