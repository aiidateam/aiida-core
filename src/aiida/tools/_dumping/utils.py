###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Helper classes and functions for the dumping feature."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, Type, Union

# typing.assert_never available since 3.11
from typing_extensions import assert_never

from aiida import orm
from aiida.common import AIIDA_LOGGER, timezone
from aiida.manage.configuration import Profile
from aiida.tools._dumping.config import DumpMode, GroupDumpConfig, ProcessDumpConfig, ProfileDumpConfig

# Optional support for aiida-workgraph
try:
    from aiida_workgraph.orm.workgraph import WorkGraphNode  # type: ignore[import-not-found]
    # `type: ignore` due to untyped package

    wg_available = True
except ImportError:
    wg_available = False

RegistryNameType = Literal['calculations', 'workflows', 'groups']

# Progress bar format for dump operations - wider description field to avoid truncation
DUMP_PROGRESS_BAR_FORMAT = '{desc:60.60}{percentage:6.1f}%|{bar}| {n_fmt}/{total_fmt}'

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

# Register WorkGraphNode if aiida-workgraph is available
# Note: WorkGraphNode inherits from WorkChainNode, so isinstance checks throughout the codebase work correctly
if wg_available:
    ORM_TYPE_TO_REGISTRY[WorkGraphNode] = 'workflows'

logger = AIIDA_LOGGER.getChild('tools._dumping.utils')


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
        return cls(last=last)


@dataclass
class ProcessingQueue:
    """Queue/store for nodes to be dumped."""

    calculations: list = field(default_factory=list)
    workflows: list = field(default_factory=list)

    def __len__(self) -> int:
        """Return total number of calculations and workflows."""
        return len(self.calculations) + len(self.workflows)

    def is_empty(self) -> bool:
        """Return True if queue contains no items."""
        return len(self) == 0

    def all_process_nodes(self) -> list[orm.ProcessNode]:
        """Get all calculations and workflows as a single list.

        :return: List of all calculations and workflows in the ``ProcessingQueue``.
        """
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
    new_label: str | None
    old_path: Path
    new_path: Path


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
    """Holds changes related to individual nodes."""

    # Nodes detected as new or modified that require dumping
    new_or_modified: ProcessingQueue = field(default_factory=ProcessingQueue)
    # List of UUIDs of deleted nodes
    deleted: Set[str] = field(default_factory=set)


@dataclass
class DumpChanges:
    """All detected changes for a dump cycle."""

    nodes: NodeChanges = field(default_factory=NodeChanges)
    groups: GroupChanges = field(default_factory=GroupChanges)

    def is_empty(self) -> bool:
        """Any node or group changes (new, deleted, modified, renamed, membership).

        :return: True if no node or group changes since the last dump
        """
        total_len = (
            len(self.nodes.deleted)
            + len(self.nodes.new_or_modified)
            + len(self.groups.new)
            + len(self.groups.deleted)
            + len(self.groups.modified)
            + len(self.groups.renamed)
            + len(self.groups.node_membership)
        )

        return total_len == 0

    def to_table(self) -> str:
        """Generate a tabulated summary of all changes in this dump cycle.

        :return: A formatted string containing tables that summarize the changes
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
        group_rows.append(['Groups', len(self.groups.renamed), 'renamed'])

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
        return f'Anticipated dump changes\n========================\n\nNodes:\n{node_table}\n\nGroups:\n{group_table}'


class DumpPaths:
    """Manages the generation of paths and directory structures for an AiiDA dump."""

    GROUPS_DIR_NAME = 'groups'
    UNGROUPED_DIR_NAME = 'ungrouped'
    CALCULATIONS_DIR_NAME = 'calculations'
    WORKFLOWS_DIR_NAME = 'workflows'
    SAFEGUARD_FILE_NAME = '.aiida_dump_safeguard'
    TRACKING_LOG_FILE_NAME = 'aiida_dump_log.json'

    def __init__(
        self,
        base_output_path: Path,
        config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig],
        dump_target_entity: Union[orm.Node, orm.Group, Profile],
    ):
        """
        Initializes the DumpPaths object for centralized path handling during the dumping.

        :param base_output_path: The absolute root path for the entire dump operation.
        :param config: The config object.
        :param dump_target_entity: The primary entity this dump operation is targeting
            This helps in contextual path decisions.
        """
        self.base_output_path: Path = base_output_path.resolve()
        self.config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig] = config
        self.dump_target_entity: Union[orm.Node, orm.Group, Profile] = dump_target_entity

    @property
    def tracking_log_file_path(self) -> Path:
        """Path to the main aiida_dump_log.json file of the dump."""
        return self.base_output_path / self.TRACKING_LOG_FILE_NAME

    def get_path_for_group(self, group: orm.Group) -> Path:
        """Get the absolute path for a group's content.

        :param group: ``orm.Group`` instance
        :return: Resolved output path for the group dump
        """

        assert isinstance(self.config, (GroupDumpConfig, ProfileDumpConfig))
        if not self.config.organize_by_groups:
            return self.base_output_path

        # If this group is the main target, it goes at the root
        if isinstance(self.dump_target_entity, orm.Group) and self.dump_target_entity.uuid == group.uuid:
            return self.base_output_path

        # Otherwise, it goes under self.GROUPS_DIR_NAME
        return self.base_output_path / self.GROUPS_DIR_NAME / group.label

    def get_path_for_node(
        self,
        node: orm.ProcessNode,
        current_content_root: Path,
    ) -> Path:
        """Determines the absolute path for dumping a specific node.

        :param node: The ``orm.ProcessNode`` object.
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
        """Determines the absolute root path for storing ungrouped nodes.

        Node type subdirectories will be created under this path.
        """
        assert isinstance(self.config, ProfileDumpConfig)
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
        group_label_part = Path(group.label)

        assert isinstance(self.config, (GroupDumpConfig, ProfileDumpConfig))
        if self.config.organize_by_groups:
            return Path(self.GROUPS_DIR_NAME) / group_label_part
        return group_label_part

    def _get_node_type_folder_name(self, node: orm.ProcessNode) -> str:
        """Obtain the corresponding subdirectory based on the node type.

        :param node: The node to be dumped
        :raises ValueError: If a node of the wrong type is being passed
        :return: The subdirectory for the given node's type as string
        """
        if isinstance(node, orm.CalculationNode):
            return self.CALCULATIONS_DIR_NAME
        elif isinstance(node, orm.WorkflowNode):
            return self.WORKFLOWS_DIR_NAME
        else:
            msg = f'Wrong node type: {type(node)} was passed.'
            raise NotImplementedError(msg)

    def _prepare_directory(self, path_to_prepare: Path, is_leaf_node_dir: bool = False) -> None:
        """Prepares a directory for dumping, a previously exesting one, or creating it, including the safeguard file.

        :param path_to_prepare: The absolute directory path to prepare.
        :param is_leaf_node_dir: True if this path is for a specific node's final dump,
            False if it's an intermediate directory (like 'groups/' or 'calculations/').
        """
        if self.config.dump_mode == DumpMode.DRY_RUN:
            return

        # Handle OVERWRITE mode: delete existing leaf directories if they have safeguards,
        # directory exists and is not empty
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

    @staticmethod
    def _safe_delete_directory(path: Path) -> None:
        """Safely deletes a directory if it contains a safeguard file.

        :param path: The path to be deleted
        """

        safeguard_path = path / DumpPaths.SAFEGUARD_FILE_NAME
        if path.is_dir() and safeguard_path.is_file():
            import shutil

            shutil.rmtree(path)

    @staticmethod
    def get_directory_stats(path: Path) -> tuple[Optional[datetime], Optional[int]]:
        """Calculates the last modification time and total size of a directory.

        :param path: The directory to be analyzed
        """
        if not path.is_dir():
            return None, None

        total_size = 0
        latest_mtime_ts = 0.0

        for dirpath, _, filenames in os.walk(path):
            for filename in filenames:
                filepath = Path(dirpath) / filename
                if filepath.is_symlink():
                    # Skip symlinks for size, but consider their mtime if needed
                    # For mtime, one might want to check the link's mtime: os.lstat(filepath).st_mtime
                    # or target's mtime if resolved: filepath.stat().st_mtime
                    # For simplicity, we use lstat for links
                    current_mtime_ts = os.lstat(filepath).st_mtime
                else:
                    stat_info = filepath.stat()
                    total_size += stat_info.st_size
                    current_mtime_ts = stat_info.st_mtime

                latest_mtime_ts = max(current_mtime_ts, latest_mtime_ts)

        if latest_mtime_ts > 0:
            # Create naive datetime from timestamp, then make it timezone-aware
            naive_datetime = datetime.fromtimestamp(latest_mtime_ts)
            dir_mtime = timezone.make_aware(naive_datetime)
        return dir_mtime, total_size

    @staticmethod
    def get_default_dump_path(
        entity: Union[orm.ProcessNode, Profile, orm.Group],
        prefix: Optional[str] = None,
        appendix: Optional[str] = None,
    ) -> Path:
        """Generate default dump path for any supported entity type.
        :param entity: The entity to be dumped
        :param prefix: Optional prefix to the default path, defaults to None
        :param appendix: Optional appendix to the default path, defaults to None
        :raises NotImplementedError: If not an entity node type is passed that is not yet supported
        :return: The default dump path for the passed entity
        """
        if isinstance(entity, orm.ProcessNode):
            return DumpPaths._get_process_node_path(entity, prefix, appendix)
        elif isinstance(entity, orm.Group):
            return DumpPaths._get_group_path(entity, prefix, appendix)
        elif isinstance(entity, Profile):
            return DumpPaths._get_profile_path(entity, prefix, appendix)
        else:
            assert_never(entity)

    @staticmethod
    def _get_process_node_path(process_node: orm.ProcessNode, prefix: Optional[str], appendix: Optional[str]) -> Path:
        """Generate the default dump path for ``orm.ProcessNode``.

        :param process_node: The ``orm.ProcessNode`` to be dumped
        :param prefix: Optional prefix to the default dump path to be created
        :param appendix: Optional appendix to the default dump path to be created
        :return: The default dump path for the given ``orm.ProcessNode``
        """
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

    @staticmethod
    def _get_profile_path(profile: Profile, prefix: Optional[str], appendix: Optional[str]) -> Path:
        """Generate the default dump path for a ``Profile``.

        :param profile: The ``Profile`` to be dumped
        :param prefix: Optional prefix to the default dump path to be created
        :param appendix: Optional appendix to the default dump path to be created
        :return: The default dump path for the given ``Profile``
        """
        label_elements = []

        if prefix:
            label_elements.append(prefix)
        label_elements.append(profile.name)
        if appendix:
            label_elements.append(appendix)

        return Path('-'.join(label_elements))

    @staticmethod
    def _get_group_path(group: orm.Group, prefix: Optional[str], appendix: Optional[str]) -> Path:
        """Generate the default dump path for an ``orm.Group``.

        :param group: The ``orm.Group`` to be dumped
        :param prefix: Optional prefix to the default dump path to be created
        :param appendix: Optional appendix to the default dump path to be created
        :return: The default dump path for the given ``orm.Group``
        """
        label_elements = []

        if prefix:
            label_elements.append(prefix)
        label_elements.append(group.label)
        if appendix:
            label_elements.append(appendix)

        return Path('-'.join(label_elements))
