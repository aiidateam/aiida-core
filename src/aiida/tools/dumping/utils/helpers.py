###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Helper classes for the dumping feature."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Set, Type, Union

from aiida import orm
from aiida.common import timezone

RegistryNameType = Literal['calculations', 'workflows', 'groups']


if TYPE_CHECKING:
    pass

REGISTRY_TO_ORM_TYPE: dict[str, Type[Union[orm.CalculationNode, orm.WorkflowNode, orm.Group]]] = {
    'calculations': orm.CalculationNode,
    'workflows': orm.WorkflowNode,
    'groups': orm.Group,
}

ORM_TYPE_TO_REGISTRY = {
    orm.CalculationNode: 'calculations',
    orm.CalcFunctionNode: 'calculations',
    orm.CalcJobNode: 'calculations',
    orm.WorkflowNode: 'workflows',
    orm.WorkFunctionNode: 'workflows',
    orm.WorkChainNode: 'workflows',
    orm.Group: 'groups',
}

__all__ = (
    'ORM_TYPE_TO_REGISTRY',
    'REGISTRY_TO_ORM_TYPE',
    'DumpTimes',
    'DumpTimes',
    'GroupChanges',
    'GroupInfo',
    'GroupRenameInfo',
    'NodeChanges',
    'NodeMembershipChange',
    'ProcessingQueue',
    'RegistryNameType',
)


@dataclass
class DumpTimes:
    """Holds relevant timestamps for a dump operation."""

    current: datetime = field(default_factory=timezone.now)
    last: Optional[datetime] = None

    @classmethod
    def from_last_log_time(cls, last_log_time: str | None) -> 'DumpTimes':
        """Create DumpTimes initializing `last` from an ISO time string."""
        last = None
        if last_log_time:
            last = datetime.fromisoformat(last_log_time)
        return cls(last=last)


@dataclass
class ProcessingQueue:
    """Queue/stroe for nodes to be dumped."""

    calculations: list = field(default_factory=list)
    workflows: list = field(default_factory=list)
    groups: list = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.calculations) + len(self.workflows) + len(self.groups)

    def is_empty(self) -> bool:
        return len(self) == 0

    def all_process_nodes(self) -> list[orm.ProcessNode]:
        """Get all calculations and workflows as a single list."""
        return self.calculations + self.workflows


@dataclass
class GroupInfo:
    """Information about a group (typically for new or deleted groups)."""

    uuid: str
    node_count: int = 0
    label: Optional[str] = None


@dataclass
class GroupModificationInfo:
    """Information about modifications to an existing group's membership."""

    uuid: str
    label: str
    nodes_added: List[str] = field(default_factory=list)
    nodes_removed: List[str] = field(default_factory=list)


@dataclass
class NodeMembershipChange:
    """Details how a specific node's group membership changed."""

    added_to: List[str] = field(default_factory=list)
    removed_from: List[str] = field(default_factory=list)


@dataclass
class GroupRenameInfo:
    """Information about a group that has been renamed."""

    uuid: str
    old_path: Path
    new_path: Path
    new_label: str | None


@dataclass
class GroupChanges:
    """Holds all changes related to group lifecycle and membership."""

    deleted: List[GroupInfo] = field(default_factory=list)
    new: List[GroupInfo] = field(default_factory=list)
    modified: List[GroupModificationInfo] = field(default_factory=list)
    renamed: List[GroupRenameInfo] = field(default_factory=list)
    node_membership: Dict[str, NodeMembershipChange] = field(default_factory=dict)


@dataclass
class NodeChanges:
    """Holds changes related to individual nodes (Calc, Work, Data)."""

    # Nodes detected as new or modified that require dumping
    new_or_modified: ProcessingQueue = field(default_factory=ProcessingQueue)
    # UUIDs of *nodes* detected as deleted from the database
    # Note: We separate deleted nodes from deleted groups based on Option 1.
    # If you need deleted group UUIDs elsewhere (like DeletionExecutor),
    # they are available in GroupChangeInfo.deleted[...].uuid
    deleted: Set[str] = field(default_factory=set)


@dataclass
class DumpChanges:
    """Represents all detected changes for a dump cycle (Recommended Structure)."""

    nodes: NodeChanges = field(default_factory=NodeChanges)
    groups: GroupChanges = field(default_factory=GroupChanges)

    def is_empty(self) -> bool:
        total_len = (
            len(self.nodes.deleted)
            + len(self.nodes.new_or_modified)
            + len(self.groups.deleted)
            + len(self.groups.new)
            + len(self.groups.modified)
            + len(self.groups.renamed)
            + len(self.groups.node_membership)
        )

        return total_len == 0

    def to_table(self) -> str:
        """Generate a tabulated summary of all changes in this dump cycle.

        Returns:
            str: A formatted string containing tables that summarize the changes.
        """
        from tabulate import tabulate

        # --- Node Changes Table ---
        node_rows = []

        # Add new or modified nodes by type
        new_calcs = len(self.nodes.new_or_modified.calculations)
        new_workflows = len(self.nodes.new_or_modified.workflows)
        total_new = new_calcs + new_workflows

        node_rows.append(['Calculations', new_calcs, 'new/modified'])
        node_rows.append(['Workflows', new_workflows, 'new/modified'])
        node_rows.append(['Total', total_new, 'new/modified'])

        # Add deleted nodes
        node_rows.append(['Nodes', len(self.nodes.deleted), 'deleted'])

        node_table = tabulate(
            node_rows,
            headers=['Entity Type', 'Count', 'Status'],
            tablefmt='simple',
        )

        # --- Group Changes Table ---
        group_rows = []

        # New, modified and deleted groups
        group_rows.append(['Groups', len(self.groups.new), 'new'])
        group_rows.append(['Groups', len(self.groups.modified), 'modified'])
        group_rows.append(['Groups', len(self.groups.deleted), 'deleted'])

        # Count node membership changes
        nodes_added_to_groups = sum(len(change.added_to) for change in self.groups.node_membership.values())
        nodes_removed_from_groups = sum(len(change.removed_from) for change in self.groups.node_membership.values())

        group_rows.append(['Node memberships', nodes_added_to_groups, 'added'])
        group_rows.append(['Node memberships', nodes_removed_from_groups, 'removed'])

        group_table = tabulate(
            group_rows,
            headers=['Entity Type', 'Count', 'Status'],
            tablefmt='simple',
        )

        # Combine tables with a header
        return (
            'Anticipated dump changes\n'
            '========================\n\n'
            'Nodes:\n'
            f'{node_table}\n\n'
            'Groups:\n'
            f'{group_table}'
        )
