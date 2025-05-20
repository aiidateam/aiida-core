###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

"""Path utility functions and classes for the dumping feature."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiida import orm
from aiida.common import timezone
from aiida.common.log import AIIDA_LOGGER
from aiida.manage.configuration import Profile
from aiida.tools.dumping.config import DumpConfig, DumpMode

logger = AIIDA_LOGGER.getChild('tools.dumping.utils.paths')

__all__ = ('DumpPaths',)


class DumpPaths:
    """
    Manages the generation of paths and directory structures for an AiiDA dump,
    acting as a central policy for the dump layout.
    """

    # --- Constants ---
    # (Move constants like 'groups_folder_name', 'ungrouped_folder_name',
    #  'calculations_folder_name', etc., here if they are universally used)
    GROUPS_DIR_NAME = 'groups'
    UNGROUPED_DIR_NAME = 'ungrouped'
    CALCULATIONS_DIR_NAME = 'calculations'
    WORKFLOWS_DIR_NAME = 'workflows'
    DATA_DIR_NAME = 'data'
    OTHER_NODES_DIR_NAME = 'other_nodes'
    SAFEGUARD_FILE_NAME = '.aiida_dump_safeguard'
    TRACKER_FILE_NAME = 'aiida_dump_track.json'
    CONFIG_FILE_NAME = 'aiida_dump_config.yaml'

    def __init__(
        self, base_output_path: Path, config: DumpConfig, dump_target_entity: Optional[orm.Node | orm.Group] = None
    ):
        """
        Initializes the DumpPaths policy.

        :param base_output_path: The absolute root path for this entire dump operation.
                                 For a facade like `GroupDumper(group, output_path=...)`,
                                 this `base_output_path` IS the `output_path` provided to the facade.
        :param config: The DumpConfig object.
        :param dump_target_entity: The primary entity this dump operation is targeting
                                   (e.g., a specific Group if GroupDumper is used, a ProcessNode
                                   if ProcessDumper is used, or None for ProfileDumper).
                                   This helps in contextual path decisions.
        """
        self.base_output_path: Path = base_output_path.resolve()
        self.config: DumpConfig = config
        self.dump_target_entity: Optional[orm.Node | orm.Group] = dump_target_entity

    @property
    def tracker_file_path(self) -> Path:
        """Path to the main aiida_dump_track.json file."""
        return self.base_output_path / self.TRACKER_FILE_NAME

    @property
    def config_file_path(self) -> Path:
        """Path to the aiida_dump_config.yaml file."""
        return self.base_output_path / self.CONFIG_FILE_NAME

    def get_safeguard_path(self, directory: Path) -> Path:
        """Returns the path to the safeguard file within a given directory."""
        return directory / self.SAFEGUARD_FILE_NAME

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

    def get_path_for_group_content(
        self,
        group: orm.Group,
        parent_group_content_path: Optional[Path] = None,
    ) -> Path:
        if not self.config.organize_by_groups:
            return self.base_output_path

        if parent_group_content_path is None:
            if isinstance(self.dump_target_entity, orm.Group) and self.dump_target_entity.uuid == group.uuid:
                return self.base_output_path
            else:
                return self.base_output_path / self._get_group_subdirectory_segment(group)
        else:
            # For nested groups, use the direct label as the subdirectory name
            # under the parent_group_content_path.
            return parent_group_content_path / Path(group.label)

    def get_path_for_node(
        self,
        node: orm.Node,
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
        node_dir_name = self._get_node_directory_name(node)  # Uses existing static method

        # Nodes are always placed in a type-specific subdirectory *within* the
        # current_content_root. The current_content_root has already been determined
        # by get_path_for_group_content or get_path_for_ungrouped_nodes_root.
        return current_content_root / node_type_folder_name / node_dir_name

    def get_path_for_ungrouped_nodes_root(self) -> Path:
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

    # --- Helper methods for internal path component generation ---
    def _get_node_type_folder_name(self, node: orm.Node) -> str:
        if isinstance(node, orm.CalculationNode):
            return self.CALCULATIONS_DIR_NAME
        elif isinstance(node, orm.WorkflowNode):
            return self.WORKFLOWS_DIR_NAME
        elif isinstance(node, orm.Data):  # Assuming you add Data node dumping
            return self.DATA_DIR_NAME
        else:
            msg = f'Wrong node type: {type(node)} was passed.'
            raise ValueError(msg)

    @staticmethod
    def _get_node_directory_name(node: orm.ProcessNode, append_pk: bool = True) -> str:
        """
        Generates the directory name for a specific node (e.g., "NodeType-PK").
        (This can reuse your existing DumpPaths._get_default_process_dump_path logic)
        """
        # Assuming DumpPaths._get_default_process_dump_path returns a Path, get .name
        return str(DumpPaths._get_default_process_dump_path(node, append_pk=append_pk))

    # --- Filesystem Operation Methods ---
    def prepare_directory(self, path_to_prepare: Path, is_leaf_node_dir: bool = False) -> None:
        """
        Prepares a directory for dumping, creating it and a safeguard file.
        In OVERWRITE mode, if it's a leaf node directory and exists, it's deleted first.

        :param path_to_prepare: The absolute directory path to prepare.
        :param is_leaf_node_dir: True if this path is for a specific node's final dump,
                                 False if it's an intermediate directory (like 'groups/' or 'calculations/').
        """
        if self.config.dump_mode == DumpMode.DRY_RUN:
            return

        elif self.config.dump_mode == DumpMode.OVERWRITE:
            if path_to_prepare.exists():
                if os.listdir(path_to_prepare) and not (path_to_prepare / self.SAFEGUARD_FILE_NAME).exists():
                    if is_leaf_node_dir:
                        self.safe_delete_directory(path_to_prepare)
                    else:
                        msg = f'Path {path_to_prepare} exists, is not empty, but safeguard file missing.'
                        raise FileNotFoundError(msg)

        path_to_prepare.mkdir(parents=True, exist_ok=True)
        (path_to_prepare / self.SAFEGUARD_FILE_NAME).touch(exist_ok=True)
        # self.get_safeguard_path(path_to_prepare).touch(exist_ok=True)

    def safe_delete_directory(self, directory_path: Path) -> None:
        """
        Safely deletes a directory if it contains a safeguard file.
        """
        if self.config.dump_mode == DumpMode.DRY_RUN:
            # In dry run, we would report what would be deleted
            # logger.report(f"[DRY RUN] Would delete directory: {directory_path}")
            return

        safeguard = self.get_safeguard_path(directory_path)
        if directory_path.is_dir() and safeguard.is_file():
            import shutil

            try:
                shutil.rmtree(directory_path)
                # logger.info(f"Safely deleted directory: {directory_path}")
            except OSError:
                # logger.error(f"Error deleting directory {directory_path}: {e}")
                raise  # Or handle more gracefully
        elif directory_path.is_dir() and not safeguard.is_file():
            # logger.warning(
            # f"Directory {directory_path} does not contain safeguard file. Skipping deletion."
            # )
            pass  # Or raise an error
        elif not directory_path.is_dir():
            # logger.debug(f"Directory {directory_path} not found for deletion.")
            pass

    # --- Utility methods (can be static if they don't depend on config/base_path) ---
    @staticmethod
    def get_directory_stats(directory_path: Path) -> tuple[Optional[datetime], Optional[int]]:
        """
        Calculates the last modification time and total size of a directory.
        (Reuses existing logic from self.dump_paths.get_directory_stats)
        """
        # ... your existing implementation ...
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
    def _get_default_process_dump_path(
        process_node: orm.ProcessNode, prefix: str | None = None, append_pk: bool = True
    ) -> Path:
        """Simple helper function to generate the default parent-dumping directory if none given.

        This function is not called for the recursive sub-calls of `_dump_calculation` as it just creates the default
        parent folder for the dumping, if no name is given.

        :param process_node: The `ProcessNode` for which the directory is created.
        :return: The absolute default parent dump path.
        """

        path_entities = []

        if prefix is not None:
            path_entities += [prefix]

        if process_node.label:
            path_entities.append(process_node.label)
        elif process_node.process_label is not None:
            path_entities.append(process_node.process_label)
        elif process_node.process_type is not None:
            path_entities.append(process_node.process_type)

        if append_pk:
            path_entities += [str(process_node.pk)]
        return Path('-'.join(path_entities))

    @staticmethod
    def _get_default_profile_dump_path(
        profile: Profile, prefix: Optional[str] = None, appendix: Optional[str] = None
    ) -> Path:
        """_summary_

        :param profile: _description_
        :param prefix: _description_, defaults to "profile"
        :param appendix: _description_, defaults to "dump"
        :return: _description_
        """
        label_elements = []

        if prefix:
            label_elements.append(prefix)
        label_elements.append(profile.name)
        if appendix:
            label_elements.append(appendix)

        return Path('-'.join(label_elements))

    @staticmethod
    def _get_default_group_dump_path(
        group: orm.Group, prefix: Optional[str] = None, appendix: Optional[str] = None
    ) -> Path:
        label_elements = []

        if prefix:
            label_elements.append(prefix)
        label_elements.append(group.label)
        if appendix:
            label_elements.append(appendix)

        return Path('-'.join(label_elements))

    @staticmethod
    def _get_default_group_dump_path(
        group: orm.Group, prefix: Optional[str] = None, appendix: Optional[str] = None
    ) -> Path:
        label_elements = []

        if prefix:
            label_elements.append(prefix)
        label_elements.append(group.label)
        if appendix:
            label_elements.append(appendix)

        return Path('-'.join(label_elements))
