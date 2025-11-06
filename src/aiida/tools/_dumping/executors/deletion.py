###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The DeletionExecutor for the dumping feature."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from aiida.common.log import AIIDA_LOGGER
from aiida.tools._dumping.config import GroupDumpConfig, ProcessDumpConfig, ProfileDumpConfig
from aiida.tools._dumping.utils import DumpChanges, DumpPaths

logger = AIIDA_LOGGER.getChild('tools._dumping.executors.deletion')

if TYPE_CHECKING:
    from aiida.tools._dumping.mapping import GroupNodeMapping
    from aiida.tools._dumping.tracking import DumpTracker
    from aiida.tools._dumping.utils import GroupInfo


__all__ = ('DeletionExecutor',)


class DeletionExecutor:
    """Executes deletion of dumped artifacts for entities deleted from the DB."""

    def __init__(
        self,
        config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig],
        dump_paths: DumpPaths,
        dump_tracker: DumpTracker,
        dump_changes: DumpChanges,
        previous_mapping: GroupNodeMapping | None,
    ):
        """Initializes the DeletionExecutor.

        :param config: Populated config instance
        :param dump_paths: ``DumpPaths`` instance
        :param dump_tracker: ``DumpTracker`` instance
        :param dump_changes: ``DumpChanges`` instance
        :param previous_mapping: Instance of ``GroupNodeMapping`` if exists from a previous dump
        """

        self.config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig] = config
        self.dump_paths: DumpPaths = dump_paths
        self.dump_tracker: DumpTracker = dump_tracker
        self.dump_changes: DumpChanges = dump_changes
        self.previous_mapping: GroupNodeMapping | None = previous_mapping

    def _handle_deleted_entities(self) -> None:
        """Removes dump artifacts for entities marked as deleted in the ``DumpChanges`` object."""
        node_uuids_to_delete: set[str] = self.dump_changes.nodes.deleted
        group_info_to_delete: list[GroupInfo] = self.dump_changes.groups.deleted

        if not node_uuids_to_delete and not group_info_to_delete:
            return

        # Process Node Deletions (Nodes deleted directly from DB)
        if node_uuids_to_delete:
            logger.report(f'Removing artifacts for {len(node_uuids_to_delete)} deleted nodes.')
            for node_uuid in node_uuids_to_delete:
                self._delete_node_from_logger_and_disk(node_uuid)

        # Process Group Deletions (Groups deleted from DB)
        if group_info_to_delete:
            logger.report(f'Removing artifacts for {len(group_info_to_delete)} deleted groups.')
            # Extract UUIDs from the GroupInfo objects
            group_uuids_to_delete = {g.uuid for g in group_info_to_delete}
            for group_uuid in group_uuids_to_delete:
                self._delete_group_and_associated_node_logs(group_uuid)

    def _delete_node_from_logger_and_disk(self, node_uuid: str) -> None:
        """Remove a node's dump directory and log entry."""

        # Get entry if it exists in the ``DumpTracker``
        result = self.dump_tracker.get_entry(node_uuid)

        # Delete directory if it exists
        try:
            if result.path.exists():
                DumpPaths._safe_delete_directory(path=result.path)

        except (FileNotFoundError, ValueError) as e:
            logger.warning(f'Could not delete directory for node {node_uuid}: {e}')

        # Remove log entry
        self.dump_tracker.del_entry(uuid=node_uuid)

    def _delete_group_and_associated_node_logs(self, group_uuid: str) -> None:
        """Removes a group's log entry, its dump directory, and corresponding node log entries.

        :param group_uuid: UUID of the given, deleted group
        """

        assert isinstance(self.config, (GroupDumpConfig, ProfileDumpConfig))
        # Get group entry and determine path to delete
        group_entry = self.dump_tracker.registries['groups'].get_entry(group_uuid)
        path_to_delete = group_entry.path

        # Only delete directory if it's organized by groups and not the base path
        should_delete_dir = self.config.organize_by_groups and path_to_delete != self.dump_paths.base_output_path

        path_deleted = None
        if should_delete_dir:
            try:
                DumpPaths._safe_delete_directory(path=path_to_delete)
                path_deleted = path_to_delete
            except FileNotFoundError as e:
                logger.warning(f'Directory not found for deleted group {group_uuid} at {path_to_delete}: {e}')

        #  Delete Group Log Entry
        self.dump_tracker.del_entry(uuid=group_uuid)

        # Delete Node Log Entries Based on Path
        # Only proceed if we identified a group directory path (even if deletion failed)
        if path_deleted:
            # Iterate through node registries
            for registry_name, node_registry in self.dump_tracker.iter_by_type():
                if not node_registry or not hasattr(node_registry, 'entries'):
                    continue
                if registry_name == 'groups':
                    continue

                # Need to copy keys as we modify the dictionary during iteration
                node_uuids_in_store = list(node_registry.entries.keys())
                for node_uuid in node_uuids_in_store:
                    node_log_entry = node_registry.get_entry(node_uuid)

                    try:
                        # Check if the node's primary logged path is inside the deleted group path
                        if node_log_entry.path.resolve().is_relative_to(path_deleted.resolve()):
                            self.dump_tracker.del_entry(uuid=node_uuid)

                    except (OSError, ValueError):
                        # Errors can happen if paths don't exist when resolve() is called
                        msg = (
                            f'Could not resolve/compare path for node {node_uuid} '
                            '({node_log_entry.path}) relative to {path_deleted}: {e}'
                        )
                        logger.warning(msg)
