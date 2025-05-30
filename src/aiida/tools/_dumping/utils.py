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

import os
from dataclasses import dataclass, field
from datetime import datetime
from functools import singledispatch
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, Type, Union

from aiida import orm
from aiida.common import timezone
from aiida.common.log import AIIDA_LOGGER
from aiida.manage.configuration import Profile
from aiida.tools._dumping.config import DumpConfig, DumpMode

RegistryNameType = Literal['calculations', 'workflows', 'groups']


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
    'DumpPaths',
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

logger = AIIDA_LOGGER.getChild('tools.dumping.utils')

@dataclass(frozen=True)
class DumpTimes:
    """Holds relevant timestamps for a dump operation."""

    current: datetime = field(default_factory=lambda: timezone.now())
    last: Optional[datetime] = None

    @classmethod
    def from_last_log_time(cls, last_log_time: str | None) -> 'DumpTimes':
        """Create DumpTimes initializing `last` from an ISO time string."""
        last = None
        if last_log_time:
            last = datetime.fromisoformat(last_log_time)
        return cls(last=last)  # current will be set in __post_init__


@dataclass
class ProcessingQueue:
    """Queue/stroe for nodes to be dumped."""

    calculations: list = field(default_factory=list)
    workflows: list = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.calculations) + len(self.workflows)

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

        # Node Changes Table
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

        # Group Changes Table
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


class DumpPaths:
    """
    Manages the generation of paths and directory structures for an AiiDA dump,
    acting as a central policy for the dump layout.
    """

    GROUPS_DIR_NAME = 'groups'
    UNGROUPED_DIR_NAME = 'ungrouped'
    CALCULATIONS_DIR_NAME = 'calculations'
    WORKFLOWS_DIR_NAME = 'workflows'
    SAFEGUARD_FILE_NAME = '.aiida_dump_safeguard'
    TRACKING_LOG_FILE_NAME = 'aiida_dump_log.json'
    CONFIG_FILE_NAME = 'aiida_dump_config.yaml'

    def __init__(
        self,
        base_output_path: Path,
        config: DumpConfig,
        dump_target_entity: Optional[orm.Node | orm.Group | Profile] = None,
    ):
        """
        Initializes the DumpPaths.

        :param base_output_path: The absolute root path for this entire dump operation.
        :param config: The DumpConfig object.
        :param dump_target_entity: The primary entity this dump operation is targeting
            This helps in contextual path decisions.
        """
        self.base_output_path: Path = base_output_path.resolve()
        self.config: DumpConfig = config
        self.dump_target_entity: Optional[orm.Node | orm.Group | Profile] = dump_target_entity

    @property
    def tracking_log_file_path(self) -> Path:
        """Path to the main aiida_dump_log.json file."""
        return self.base_output_path / self.TRACKING_LOG_FILE_NAME

    @property
    def config_file_path(self) -> Path:
        """Path to the aiida_dump_config.yaml file."""
        return self.base_output_path / self.CONFIG_FILE_NAME

    def get_safeguard_path(self, directory: Path) -> Path:
        """Returns the path to the safeguard file within a given directory."""
        return directory / self.SAFEGUARD_FILE_NAME

    def get_path_for_group(self, group: orm.Group) -> Path:
        """Get the absolute path for a group's content."""
        if not self.config.organize_by_groups:
            return self.base_output_path

        # If this group is the main target, it goes at the root
        if isinstance(self.dump_target_entity, orm.Group) and self.dump_target_entity.uuid == group.uuid:
            return self.base_output_path

        # Otherwise, it goes under groups/
        return self.base_output_path / 'groups' / group.label

    def get_path_for_node(
        self,
        node: orm.ProcessNode,
        current_content_root: Path,
    ) -> Path:
        """
        Determines the absolute path for dumping a specific node.

        :param node: The aiida.orm.Node object.
        :param current_content_root: The absolute root path for the current context
            (e.g., a specific group's content path, or the path
            for ungrouped nodes, or the base_output_path for a
            single process dump).
        :param group_context_for_node: The group under whose direct hierarchy this node is being dumped.
            This is important if the node itself is also part of other groups,
            to decide its primary dump location vs. symlinks.
            If None, the node is considered ungrouped or dumped standalone.
        :return: Absolute Path for the node's dump directory.
        """
        node_type_folder_name = self._get_node_type_folder_name(node)
        node_dir_name = str(self.get_default_dump_path(node))

        # Nodes are always placed in a type-specific subdirectory *within* the
        # current_content_root. The current_content_root has already been determined
        # by get_path_for_group or get_path_for_ungrouped_nodes.
        return current_content_root / node_type_folder_name / node_dir_name

    def get_path_for_ungrouped_nodes(self) -> Path:
        """
        Determines the absolute root path for storing ungrouped nodes.
        Node type subdirectories will be created under this path.
        """
        if self.config.also_ungrouped:
            if self.config.organize_by_groups:
                # Ungrouped nodes go into "ungrouped/" at the top level
                return self.base_output_path / self.UNGROUPED_DIR_NAME
            else:
                # Ungrouped nodes go into type folders directly at the base_output_path
                return self.base_output_path
        else:
            # Should not be called if not dumping ungrouped, but return base as a fallback.
            return self.base_output_path

    def _get_group_subdirectory_segment(self, group: orm.Group) -> Path:
        """
        Determines the path segment for a group. If organize_by_groups is True,
        it prepends 'groups/'. Assumes group.label is filesystem-safe.
        """
        # Assuming group.label is directly usable as a directory name.
        # If special characters in group.label could be an issue,
        # you would need some form of sanitization here.
        group_label_part = Path(group.label)

        if self.config.organize_by_groups:
            return Path('groups') / group_label_part
        return group_label_part

    def _get_node_type_folder_name(self, node: orm.Node) -> str:
        if isinstance(node, orm.CalculationNode):
            return self.CALCULATIONS_DIR_NAME
        elif isinstance(node, orm.WorkflowNode):
            return self.WORKFLOWS_DIR_NAME
        else:
            msg = f'Wrong node type: {type(node)} was passed.'
            raise ValueError(msg)

    def _prepare_directory(self, path_to_prepare: Path, is_leaf_node_dir: bool = False) -> None:
        """Prepares a directory for dumping, a previously exesting one, or creating it, including the safeguard file.

        :param path_to_prepare: The absolute directory path to prepare.
        :param is_leaf_node_dir: True if this path is for a specific node's final dump,
            False if it's an intermediate directory (like 'groups/' or 'calculations/').
        """
        if self.config.dump_mode == DumpMode.DRY_RUN:
            return

        # Handle OVERWRITE mode: delete existing leaf directories if they have safeguards
        # Directory exists and is not empty
        if (
            self.config.dump_mode == DumpMode.OVERWRITE
            and is_leaf_node_dir
            and path_to_prepare.exists()
            and os.listdir(path_to_prepare)
        ):
            if (path_to_prepare / self.SAFEGUARD_FILE_NAME).exists():
                self._safe_delete_directory(path_to_prepare)
            else:
                msg = f'Path {path_to_prepare} exists, is not empty, but safeguard file missing.'
                raise FileNotFoundError(msg)

        # Create directory and safeguard file
        path_to_prepare.mkdir(parents=True, exist_ok=True)
        (path_to_prepare / self.SAFEGUARD_FILE_NAME).touch(exist_ok=True)

    def _safe_delete_directory(self, path: Path) -> None:
        """
        Safely deletes a directory if it contains a safeguard file.
        """
        if self.config.dump_mode == DumpMode.DRY_RUN:
            return

        safeguard = self.get_safeguard_path(path)
        if path.is_dir() and safeguard.is_file():
            import shutil

            shutil.rmtree(path)

    @staticmethod
    def get_directory_stats(directory_path: Path) -> tuple[Optional[datetime], Optional[int]]:
        """
        Calculates the last modification time and total size of a directory.
        """
        if not directory_path.is_dir():
            return None, None

        total_size = 0
        latest_mtime_ts = 0.0

        for dirpath, _, filenames in os.walk(directory_path):
            for filename in filenames:
                filepath = Path(dirpath) / filename
                try:
                    if filepath.is_symlink():  # Skip symlinks for size, but consider their mtime if needed
                        # For mtime, you might want to check link's mtime: os.lstat(filepath).st_mtime
                        # or target's mtime if resolved: filepath.stat().st_mtime
                        # For simplicity, let's use lstat for links
                        current_mtime_ts = os.lstat(filepath).st_mtime
                    else:
                        stat_info = filepath.stat()
                        total_size += stat_info.st_size
                        current_mtime_ts = stat_info.st_mtime

                    latest_mtime_ts = max(current_mtime_ts, latest_mtime_ts)
                except FileNotFoundError:
                    continue  # File might have been deleted during walk

        dir_mtime = datetime.fromtimestamp(latest_mtime_ts, tz=timezone.utc) if latest_mtime_ts > 0 else None
        return dir_mtime, total_size

    @staticmethod
    def get_default_dump_path(
        entity: Union[orm.ProcessNode, Profile, orm.Group],
        prefix: Optional[str] = None,
        appendix: Optional[str] = None,
    ) -> Path:
        """Generate default dump path for any supported entity type.

        :param entity: The entity (ProcessNode, Profile, or Group) to generate path for
        :param prefix: Optional prefix for the path
        :param appendix: Optional appendix for the path
        :return: The default dump path
        """
        return _get_default_dump_path(entity, prefix, appendix)


@singledispatch
def _get_default_dump_path(entity, prefix: Optional[str], appendix: Optional[str]) -> Path:
    """Single dispatch implementation for default dump paths."""
    msg = f'No default dump path implementation for type {type(entity)}'
    raise NotImplementedError(msg)


@_get_default_dump_path.register
def _(process_node: orm.ProcessNode, prefix: Optional[str], appendix: Optional[str]) -> Path:
    """Generate default dump path for ProcessNode."""
    path_entities = []

    if prefix is not None:
        path_entities.append(prefix)

    if process_node.label:
        path_entities.append(process_node.label)
    elif process_node.process_label is not None:
        path_entities.append(process_node.process_label)
    elif process_node.process_type is not None:
        path_entities.append(process_node.process_type)

    if not appendix:
        path_entities.append(str(process_node.pk))

    return Path('-'.join(path_entities))


@_get_default_dump_path.register
def _(profile: Profile, prefix: Optional[str], appendix: Optional[str]) -> Path:
    """Generate default dump path for Profile."""
    label_elements = []

    if prefix:
        label_elements.append(prefix)
    label_elements.append(profile.name)
    if appendix:
        label_elements.append(appendix)

    return Path('-'.join(label_elements))


@_get_default_dump_path.register
def _(group: orm.Group, prefix: Optional[str], appendix: Optional[str]) -> Path:
    """Generate default dump path for Group."""
    label_elements = []

    if prefix:
        label_elements.append(prefix)
    label_elements.append(group.label)
    if appendix:
        label_elements.append(appendix)

    return Path('-'.join(label_elements))
