from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.utils import DumpChanges, DumpPaths

logger = AIIDA_LOGGER.getChild('tools.dumping.executors.deletion')

if TYPE_CHECKING:
    from aiida.tools.dumping.config import DumpConfig
    from aiida.tools.dumping.mapping import GroupNodeMapping
    from aiida.tools.dumping.tracking import DumpTracker
    from aiida.tools.dumping.utils import GroupInfo


class DeletionExecutor:
    """Executes deletion of dumped artifacts for entities deleted from the DB."""

    def __init__(
        self,
        config: DumpConfig,
        dump_paths: DumpPaths,
        dump_tracker: DumpTracker,
        dump_changes: DumpChanges,
        previous_mapping: GroupNodeMapping | None,
    ):
        """Initializes the DeletionExecutor.


        :param config: _description_
        :param dump_paths: _description_
        :param dump_tracker: _description_
        :param dump_changes: _description_
        :param previous_mapping: _description_
        """
        self.config: DumpConfig = config
        self.dump_paths: DumpPaths = dump_paths
        self.dump_tracker: DumpTracker = dump_tracker
        self.dump_changes: DumpChanges = dump_changes
        self.previous_mapping: GroupNodeMapping | None = previous_mapping

    def _handle_deleted_entities(self) -> None:
        """Removes dump artifacts for entities marked as deleted in the changes object."""
        node_uuids_to_delete: set[str] = self.dump_changes.nodes.deleted
        group_info_to_delete: list[GroupInfo] = self.dump_changes.groups.deleted

        if not node_uuids_to_delete and not group_info_to_delete:
            return

        # --- Process Node Deletions (Nodes deleted directly from DB) ---
        if node_uuids_to_delete:
            logger.report(f'Removing artifacts for {len(node_uuids_to_delete)} deleted nodes...')
            for node_uuid in node_uuids_to_delete:
                self._delete_node_from_logger_and_disk(node_uuid)

        # --- Process Group Deletions (Groups deleted from DB) ---
        if group_info_to_delete:
            logger.report(f'Removing artifacts for {len(group_info_to_delete)} deleted groups...')
            # Extract UUIDs from the GroupInfo objects
            group_uuids_to_delete = {g.uuid for g in group_info_to_delete}
            for group_uuid in group_uuids_to_delete:
                # This method now also handles associated node log entries
                self._delete_group_and_associated_node_logs(group_uuid)

    def _delete_node_from_logger_and_disk(self, node_uuid: str) -> None:
        """Remove a node's dump directory and log entry."""

        # Get entry and store type in one call (using simplified tracker interface)
        result = self.dump_tracker.get_entry(node_uuid)
        if not result:
            return

        # Delete directory if it exists
        try:
            if result.path.exists():
                rel_path = result.path.relative_to(self.dump_paths.base_output_path)
                logger.report(f"Deleting directory '{rel_path}' for deleted node {node_uuid}")
                self.dump_paths.safe_delete_directory(result.path)

        except (FileNotFoundError, ValueError) as e:
            logger.warning(f'Could not delete directory for node {node_uuid}: {e}')

        # Remove log entry
        try:
            self.dump_tracker.del_entry(uuid=node_uuid)
        except:
            raise

    def _delete_group_and_associated_node_logs(self, group_uuid: str) -> None:
        """
        Removes a group's log entry, its dump directory (if applicable),
        and any node log entries whose primary dump path was within that directory.

        Args:
            group_uuid: The UUID of the group deleted from the database.

        Returns:
            True if the group's log entry was successfully deleted, False otherwise.
        """
        path_deleted: Path | None = None  # Keep track of the path we deleted

        # --- 1. Delete Group Directory (if applicable) ---
        group_entry = self.dump_tracker.registries['groups'].get_entry(group_uuid)
        if group_entry:
            path_to_delete = group_entry.path
            should_delete_dir = self.config.organize_by_groups and path_to_delete != self.dump_paths.base_output_path
            if should_delete_dir:
                try:
                    try:
                        rel_path = path_to_delete.relative_to(self.dump_paths.base_output_path)
                        rel_path_str = str(rel_path)
                    except ValueError:
                        rel_path_str = str(path_to_delete)

                    logger.report(f"Deleting directory '{rel_path_str}' for deleted group UUID {group_uuid}")
                    self.dump_paths.safe_delete_directory(path=path_to_delete)
                    path_deleted = path_to_delete  # Record that we deleted this path
                except FileNotFoundError:
                    msg = (
                        'Safeguard check failed or directory not found for deleted group '
                        '{group_uuid} at {path_to_delete}: {e}'
                    )
                    logger.warning(msg)
                    # If directory wasn't found, still potentially record its path for log cleanup
                    path_deleted = path_to_delete
        else:
            logger.warning(f'Log entry not found for deleted group UUID {group_uuid}. Cannot remove directory.')

        # --- 2. Delete Group Log Entry ---
        if self.dump_tracker.del_entry(uuid=group_uuid):
            pass
        else:
            logger.warning(f'Failed to remove log entry for deleted group {group_uuid} (may have been missing).')

        # Delete Node Log Entries Based on Path ---
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
                    if not node_log_entry:
                        continue

                    try:
                        # Check if the node's primary logged path is inside the deleted group path
                        # Use resolve() for robust comparison, handle potential errors
                        if node_log_entry.path.resolve().is_relative_to(path_deleted.resolve()):
                            self.dump_tracker.del_entry(uuid=node_uuid)

                    except (OSError, ValueError):
                        # Errors can happen if paths don't exist when resolve() is called
                        msg = (
                            f'Could not resolve/compare path for node {node_uuid} '
                            '({node_log_entry.path}) relative to {path_deleted}: {e}'
                        )
                        logger.warning(msg)
