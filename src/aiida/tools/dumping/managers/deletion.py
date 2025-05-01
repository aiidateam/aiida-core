from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.utils.helpers import DumpChanges
from aiida.tools.dumping.utils.paths import DumpPaths

logger = AIIDA_LOGGER.getChild('tools.dumping.managers.deletion')

if TYPE_CHECKING:
    from aiida.tools.dumping.config import DumpConfig
    from aiida.tools.dumping.logger import DumpLogger
    from aiida.tools.dumping.mapping import GroupNodeMapping
    from aiida.tools.dumping.utils.helpers import GroupInfo


class DeletionManager:
    """Executes deletion of dumped artifacts for entities deleted from the DB."""

    def __init__(
        self,
        config: DumpConfig,
        dump_paths: DumpPaths,
        dump_logger: DumpLogger,
        dump_changes: DumpChanges,
        stored_mapping: GroupNodeMapping | None,
    ):
        """Initializes the DeletionManager.


        :param config: _description_
        :param dump_paths: _description_
        :param dump_logger: _description_
        :param dump_changes: _description_
        :param stored_mapping: _description_
        """
        self.config: DumpConfig = config
        self.dump_paths: DumpPaths = dump_paths
        self.dump_logger: DumpLogger = dump_logger
        self.dump_changes: DumpChanges = dump_changes
        self.stored_mapping: GroupNodeMapping | None = stored_mapping

    def _handle_deleted_entities(self) -> bool:
        """
        Removes dump artifacts for entities marked as deleted in the changes object.

        Args:
            changes: Object containing the detected node and group deletions.

        Returns:
            True if any deletion action (directory or log entry) was performed, False otherwise.
        """
        node_uuids_to_delete: set[str] = self.dump_changes.nodes.deleted
        group_info_to_delete: list[GroupInfo] = self.dump_changes.groups.deleted

        if not node_uuids_to_delete and not group_info_to_delete:
            logger.info('No deleted entities identified in changes object.')
            return False

        logger.info('Processing deletions based on detected changes...')
        something_deleted = False

        # --- Process Node Deletions (Nodes deleted directly from DB) ---
        if node_uuids_to_delete:
            logger.report(f'Removing artifacts for {len(node_uuids_to_delete)} deleted nodes...')
            for node_uuid in node_uuids_to_delete:
                if self._delete_node_from_logger_and_disk(node_uuid):
                    something_deleted = True
        else:
            logger.info('No deleted nodes to process.')

        # --- Process Group Deletions (Groups deleted from DB) ---
        if group_info_to_delete:
            logger.report(f'Removing artifacts for {len(group_info_to_delete)} deleted groups...')
            # Extract UUIDs from the GroupInfo objects
            group_uuids_to_delete = {g.uuid for g in group_info_to_delete}
            for group_uuid in group_uuids_to_delete:
                # This method now also handles associated node log entries
                if self._delete_group_and_associated_node_logs(group_uuid):
                    something_deleted = True
        else:
            logger.info('No deleted groups to process.')

        return something_deleted

    def _delete_node_from_logger_and_disk(self, uuid: str) -> bool:
        """
        Helper to remove a node's primary dump directory and its entire log entry.

        Returns:
            True if the node's log entry was successfully deleted, False otherwise.
        """
        store = self.dump_logger.get_store_by_uuid(uuid)
        if not store:
            # It might have already been deleted if associated with a deleted group below
            logger.debug(
                f'Log store not found for deleted node UUID {uuid} (might be expected). Cannot remove further.'
            )
            return False  # Indicate log entry wasn't deleted *by this call*

        entry = store.get_entry(uuid)
        if not entry:
            logger.warning(f'Log entry not found for node UUID {uuid} in its store. Cannot remove.')
            return False  # Indicate log entry wasn't deleted

        path_to_delete = entry.path
        # Determine store key for deletion from logger
        store_key = next(
            (
                s_name
                for s_name in ['calculations', 'workflows', 'data']
                if getattr(self.dump_logger, s_name, None) == store
            ),
            None,
        )
        if not store_key:
            logger.error(f'Consistency error: Could not determine store key name for node {uuid}.')
            # Try deleting log entry anyway? Or return False? Let's try deleting.
            # Fallback: Attempt deletion without knowing the exact store key (less ideal)
            # deleted_from_log = store.del_entry(uuid) # Assumes store has del_entry
            # For now, return False as we couldn't guarantee deletion from the main logger structure
            return False

        deleted_from_log = False
        try:
            # Attempt to delete directory first (use appropriate safeguard)
            # TODO: Adjust safeguard if Data nodes use a different one
            rel_path = path_to_delete.relative_to(self.dump_paths.parent)
            msg = f"Deleting directory '{rel_path}' for deleted node UUID {uuid}"
            logger.report(msg)
            DumpPaths._safe_delete_dir(path=path_to_delete, safeguard_file=DumpPaths.safeguard_file)
        except FileNotFoundError as e:
            logger.warning(
                f'Directory or safeguard file not found for deleted node {uuid} at {path_to_delete}: {e}. '
                f'Proceeding to remove log entry.'
            )
        except Exception as e:
            logger.error(
                f'Failed to delete directory for deleted node {uuid} at {path_to_delete}: {e}. '
                f'Proceeding to remove log entry.',
                exc_info=True,
            )
        finally:
            # Always attempt to remove the log entry
            if self.dump_logger.del_entry(store_key=store_key, uuid=uuid):
                logger.debug(f"Removed log entry for deleted node {uuid} from store '{store_key}'.")
                deleted_from_log = True
            else:
                # This might happen if it was already removed via group deletion logic
                logger.debug(
                    f'Log entry for deleted node {uuid} potentially already removed '
                    f'(e.g., via group deletion). Store: {store_key}.'
                )

        return deleted_from_log

    def _delete_group_and_associated_node_logs(self, group_uuid: str) -> bool:
        """
        Removes a group's log entry, its dump directory (if applicable),
        and any node log entries whose primary dump path was within that directory.

        Args:
            group_uuid: The UUID of the group deleted from the database.

        Returns:
            True if the group's log entry was successfully deleted, False otherwise.
        """
        group_log_deleted = False
        path_deleted: Path | None = None  # Keep track of the path we deleted

        # --- 1. Delete Group Directory (if applicable) ---
        group_entry = self.dump_logger.groups.get_entry(group_uuid)
        if group_entry:
            path_to_delete = group_entry.path
            should_delete_dir = self.config.organize_by_groups and path_to_delete != self.dump_paths.absolute
            if should_delete_dir:
                try:
                    rel_path_str = 'unknown'
                    try:
                        rel_path = path_to_delete.relative_to(self.dump_paths.absolute)
                        rel_path_str = str(rel_path)
                    except ValueError:
                        rel_path_str = str(path_to_delete)

                    logger.report(f"Deleting directory '{rel_path_str}' for deleted group UUID {group_uuid}")
                    DumpPaths._safe_delete_dir(path=path_to_delete, safeguard_file=DumpPaths.safeguard_file)
                    path_deleted = path_to_delete  # Record that we deleted this path
                except FileNotFoundError:
                    msg = (
                        'Safeguard check failed or directory not found for deleted group '
                        '{group_uuid} at {path_to_delete}: {e}'
                    )
                    logger.warning(msg)
                    # If directory wasn't found, still potentially record its path for log cleanup
                    path_deleted = path_to_delete
                except Exception as e:
                    logger.error(
                        f'Failed to delete directory for deleted group {group_uuid} at {path_to_delete}: {e}',
                        exc_info=True,
                    )
            else:
                logger.debug(f'Not deleting directory for group {group_uuid} (flat structure or root path).')
        else:
            logger.warning(f'Log entry not found for deleted group UUID {group_uuid}. Cannot remove directory.')

        # --- 2. Delete Group Log Entry ---
        if self.dump_logger.del_entry(store_key='groups', uuid=group_uuid):
            logger.debug(f'Removed log entry for deleted group {group_uuid}.')
            group_log_deleted = True
        else:
            logger.warning(f'Failed to remove log entry for deleted group {group_uuid} (may have been missing).')

        # --- 3. NEW: Delete Node Log Entries Based on Path ---
        nodes_removed_count = 0
        # Only proceed if we identified a group directory path (even if deletion failed)
        if path_deleted:
            logger.info(f'Scanning node logs for entries within deleted group path: {path_deleted}')
            # Iterate through all potential node stores
            for store_key in ['calculations', 'workflows', 'data']:
                node_store = getattr(self.dump_logger, store_key, None)
                if not node_store or not hasattr(node_store, 'entries'):
                    continue

                # Need to copy keys as we modify the dictionary during iteration
                node_uuids_in_store = list(node_store.entries.keys())
                for node_uuid in node_uuids_in_store:
                    node_log_entry = node_store.get_entry(node_uuid)
                    if not node_log_entry or not node_log_entry.path:
                        continue  # Skip if entry or path is missing

                    try:
                        # Check if the node's primary logged path is inside the deleted group path
                        # Use resolve() for robust comparison, handle potential errors
                        if node_log_entry.path.resolve().is_relative_to(path_deleted.resolve()):
                            msg = (
                                f"Node {node_uuid} path '{node_log_entry.path}' is within deleted "
                                "group path '{path_deleted}'. Removing log entry."
                            )
                            logger.debug(msg)
                            if self.dump_logger.del_entry(store_key=store_key, uuid=node_uuid):
                                nodes_removed_count += 1
                            # else: No warning needed if removal fails, might be race condition or prior removal
                    except (OSError, ValueError):
                        # Errors can happen if paths don't exist when resolve() is called
                        msg = (
                            f'Could not resolve/compare path for node {node_uuid} '
                            '({node_log_entry.path}) relative to {path_deleted}: {e}'
                        )
                        logger.warning(msg)
                    except Exception as e:
                        logger.error(f'Unexpected error checking path for node {node_uuid}: {e}', exc_info=True)

            if nodes_removed_count > 0:
                msg = (
                    f'Removed log entries for {nodes_removed_count} nodes whose dump path was within '
                    f"the deleted group directory '{path_deleted.name}'."
                )
                logger.report(msg)
        else:
            msg = (
                f'No group directory path identified for deleted group {group_uuid}. '
                'Skipping path-based node log cleanup.'
            )
            logger.debug(msg)

        # Note: The previous logic using stored_mapping is removed as this path-based approach is more direct.

        return group_log_deleted
