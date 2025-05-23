###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Manager that orchestrates dumping an AiiDA profile."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.common.progress_reporter import get_progress_reporter, set_progress_bar_tqdm
from aiida.orm import Group, WorkflowNode
from aiida.tools.dumping.detect import DumpChangeDetector
from aiida.tools.dumping.tracking import DumpRecord, DumpTracker
from aiida.tools.dumping.utils.helpers import DumpChanges, DumpNodeStore
from aiida.tools.dumping.utils.paths import DumpPaths

if TYPE_CHECKING:
    from aiida.tools.dumping.config import DumpConfig
    from aiida.tools.dumping.executors.process import ProcessDumpExecutor
    from aiida.tools.dumping.mapping import GroupNodeMapping
    from aiida.tools.dumping.tracking import DumpTracker
    from aiida.tools.dumping.utils.helpers import GroupChanges, GroupModificationInfo

logger = AIIDA_LOGGER.getChild('tools.dumping.managers.collection')


class CollectionDumpExecutor:
    def __init__(
        self,
        config: DumpConfig,
        dump_paths: DumpPaths,
        dump_tracker: DumpTracker,
        process_manager: ProcessDumpExecutor,
        current_mapping: GroupNodeMapping,
    ) -> None:
        self.config: DumpConfig = config
        self.dump_paths: DumpPaths = dump_paths
        self.process_manager: ProcessDumpExecutor = process_manager
        self.current_mapping: GroupNodeMapping = current_mapping
        self.dump_tracker: DumpTracker = dump_tracker

    def _register_group_and_prepare_path(self, group: orm.Group, group_content_path: Path) -> None:
        """
        Ensures the group's specific content directory is prepared and the group is logged
        with its absolute content path.
        """
        # Directory preparation for group_content_path is now expected to be done
        # by the caller (e.g., GroupDumpExecutor.dump() or ProfileDumpExecutor loop)
        # using self.dump_paths.prepare_directory().
        # However, this method is also where the logger entry is made, so it's crucial.

        # Ensure the directory exists (might be redundant if caller prepares, but safe)
        # In non-dry_run modes, prepare_directory also creates the safeguard.
        self.dump_paths.prepare_directory(group_content_path, is_leaf_node_dir=False)

        if group.uuid not in self.dump_tracker.groups.entries:
            logger.debug(
                f"Registering group '{group.label}' ({group.uuid}) in logger "
                f'with content path: {group_content_path}'
            )
            self.dump_tracker.add_entry(
                store_key='groups',
                uuid=group.uuid,
                entry=DumpRecord(path=group_content_path),  # Log the absolute path
            )
        # else: Group already logged. Path updates due to renames should be handled
        # by the group rename logic (e.g., in _handle_group_changes or DumpTracker.update_paths)

    def _identify_nodes_for_group(self, group: Group, changes: DumpChanges) -> tuple[DumpNodeStore, list[WorkflowNode]]:
        """Identifies nodes explicitly belonging to a given group from the provided changes."""
        # (Implementation of this method can remain largely the same,
        # as it filters `changes` based on `self.current_mapping`)
        nodes_explicitly_in_group = DumpNodeStore()
        # self.current_mapping should be scoped appropriately by the calling manager
        # or reflect the global state if that's intended for this call.
        group_node_uuids = self.current_mapping.group_to_nodes.get(group.uuid, set())
        workflows_explicitly_in_group: list[WorkflowNode] = []

        for store_key in ['calculations', 'workflows', 'data']:  # Assuming 'data' might be added
            # `changes.nodes.new_or_modified` should be the set of nodes
            # identified by DumpEngine for the current operation (e.g., all new nodes in profile,
            # or all new nodes within a specific group if detector was scoped).
            globally_detected_nodes = getattr(changes.nodes.new_or_modified, store_key, [])
            filtered_nodes = [node for node in globally_detected_nodes if node.uuid in group_node_uuids]
            if filtered_nodes:
                setattr(nodes_explicitly_in_group, store_key, filtered_nodes)
                if store_key == 'workflows':
                    workflows_explicitly_in_group.extend(
                        cast(
                            list[WorkflowNode],
                            [wf for wf in filtered_nodes if isinstance(wf, orm.WorkflowNode)],
                        )
                    )
        return nodes_explicitly_in_group, workflows_explicitly_in_group

    def _dump_group_descendants(
        self,
        group: Group,
        workflows_in_group: list[WorkflowNode],
        current_group_content_root: Path,  # Nodes are dumped into this root
    ) -> None:
        """
        Finds and dumps calculation descendants for the group's workflows
        into the 'current_group_content_root'.
        """
        if self.config.only_top_level_calcs or not workflows_in_group:
            return

        logger.debug(
            f"Finding calculation descendants for workflows in group '{group.label}' "
            f"(only_top_level_calcs=False), to be dumped into '{current_group_content_root}'"
        )
        try:
            # _get_calculation_descendants is a static method in DumpChangeDetector
            descendants = DumpChangeDetector._get_calculation_descendants(workflows_in_group)
            if not descendants:
                logger.debug(f"No calculation descendants found for workflows in group '{group.label}'.")
                return

            logged_calc_uuids = set(self.dump_tracker.calculations.entries.keys())
            unique_unlogged_descendants = [desc for desc in descendants if desc.uuid not in logged_calc_uuids]

            if unique_unlogged_descendants:
                logger.info(
                    f'Immediately dumping {len(unique_unlogged_descendants)} unique, '
                    f"unlogged calculation descendants for group '{group.label}'."
                )
                descendant_store = DumpNodeStore(calculations=unique_unlogged_descendants)
                # Descendants are dumped with the group context, into the group's content root.
                self._dump_nodes(
                    node_store=descendant_store,
                    group_context=group,
                    current_dump_root_for_nodes=current_group_content_root,
                )
            else:
                logger.debug(f"All descendants for group '{group.label}' were already logged.")
        except Exception as e:
            logger.warning(
                f"Could not retrieve/process/dump descendants for group '{group.label}': {e}",
                exc_info=True,
            )

    def _dump_nodes(
        self,
        node_store: DumpNodeStore,
        group_context: Optional[orm.Group] = None,
        current_dump_root_for_nodes: Optional[Path] = None,
    ):
        """
        Dumps a collection of nodes. Nodes are placed relative to 'current_dump_root_for_nodes'.
        """
        set_progress_bar_tqdm()
        nodes_to_dump = []
        nodes_to_dump.extend(node_store.calculations)
        nodes_to_dump.extend(node_store.workflows)
        if not nodes_to_dump:
            return

        desc = f'Dumping {len(nodes_to_dump)} nodes'
        if group_context:
            desc += f" for group '{group_context.label}'"
        logger.report(desc)

        if current_dump_root_for_nodes is None:
            # This is a fallback, the caller should ideally always provide the explicit root.
            if group_context:
                current_dump_root_for_nodes = self.dump_paths.get_path_for_group_content(group_context)
            else:  # Ungrouped nodes
                current_dump_root_for_nodes = self.dump_paths.get_path_for_ungrouped_nodes_root()
            logger.warning(f'current_dump_root_for_nodes was None, derived as: {current_dump_root_for_nodes}')

        with get_progress_reporter()(desc=desc, total=len(nodes_to_dump)) as progress:
            for node in nodes_to_dump:
                try:
                    # Determine the specific, absolute path for this node's dump directory
                    node_specific_dump_path = self.dump_paths.get_path_for_node(
                        node=node,
                        current_content_root=current_dump_root_for_nodes,
                    )
                    # ProcessManager.dump takes the final, specific path for the node.
                    self.process_manager.dump(
                        process_node=node,
                        target_path=node_specific_dump_path,
                    )
                except Exception:
                    raise
                finally:
                    progress.update()

    def _process_group(self, group: Group, changes: DumpChanges, group_content_root_path: Path) -> None:
        """
        Process a single group: find its nodes, dump descendants, dump explicit nodes,
        all operating within the provided 'group_content_root_path'.

        :param group: The orm.Group to process.
        :param changes: DumpChanges object, hopefully scoped to this group or the current operation.
        :param group_content_root_path: The absolute filesystem path where this group's
            direct content (safeguard, type subdirs) should reside.
        """
        logger.debug(
            f"Processing group: '{group.label}' ({group.uuid}) " f"with content root: '{group_content_root_path}'"
        )

        # Ensure the group's own content directory is prepared and logged.
        # _register_group_and_prepare_path should use group_content_root_path.
        self._register_group_and_prepare_path(group=group, group_content_path=group_content_root_path)

        # 1. Identify nodes explicitly in this group from the (hopefully scoped) changes.
        nodes_explicitly_in_group, workflows_in_group = self._identify_nodes_for_group(group, changes)

        # 2. Find and immediately dump calculation descendants if required.
        # These are dumped into the group_content_root_path.
        self._dump_group_descendants(
            group=group, workflows_in_group=workflows_in_group, current_group_content_root=group_content_root_path
        )

        # 3. Dump the nodes explicitly identified for this group.
        store_for_explicit_dump = DumpNodeStore(
            calculations=nodes_explicitly_in_group.calculations,
            workflows=nodes_explicitly_in_group.workflows,
        )

        if len(store_for_explicit_dump) > 0:
            logger.info(f"Dumping {len(store_for_explicit_dump)} explicitly identified nodes for group '{group.label}'")
            try:
                # These nodes are dumped into the group_content_root_path.
                self._dump_nodes(
                    node_store=store_for_explicit_dump,
                    group_context=group,
                    current_dump_root_for_nodes=group_content_root_path,
                )
            except Exception as e:
                logger.error(
                    f"Error dumping explicitly identified nodes for group '{group.label}': {e}",
                    exc_info=True,
                )
        else:
            logger.debug(
                f"No further explicitly identified nodes to dump in group '{group.label}' "
                'after handling descendants.'
            )

    def _handle_group_changes(self, group_changes: GroupChanges):
        """Handle changes in the group structure since the last dump.

        Apart from membership changes in the group-node mapping, this doesn't do much else actual work, as the actual
        dumping and deleting are handled in other places.

        :param group_changes: _description_
        """
        logger.report('Processing group changes...')

        # 1. Handle Deleted Groups (Directory deletion handled by DeletionExecutor)
        # We might still need to log this or perform other cleanup
        if group_changes.deleted:
            group_labels = [group_info.label for group_info in group_changes.deleted]
            msg = f'Detected {len(group_changes.deleted)} deleted groups.'
            logger.report(msg)

        # 2. Handle New Groups
        if group_changes.new:
            group_labels = [group_info.label for group_info in group_changes.new]
            logger.report(f'Processing {len(group_changes.new)} new or modified groups: {group_labels}')
            for group_info in group_changes.new:
                # Ensure the group directory exists and is logged
                try:
                    group = orm.load_group(uuid=group_info.uuid)
                    # Avoid creating empty directories for empty groups
                    if not group.nodes:
                        continue
                    # Avoid creating empty directories for deselected groups
                    if self.config.groups and (
                        group.label not in self.config.groups or group_info.uuid not in self.config.groups
                    ):
                        continue

                    group_path = self.dump_paths.get_path_for_group_content(group=group)
                    self._register_group_and_prepare_path(group=group, group_content_path=group_path)
                    # Dumping nodes within this new group will happen if they
                    # are picked up by the NodeChanges detection based on the config.
                except Exception as e:
                    logger.warning(f'Could not process new group {group_info.uuid}: {e}')

        # --- Handle Renamed Groups ---
        if self.config.relabel_groups and group_changes.renamed:
            logger.report(f'Processing {len(group_changes.renamed)} renamed groups...')
            for rename_info in group_changes.renamed:
                old_path = rename_info.old_path
                new_path = rename_info.new_path
                logger.info(f"Handling rename for group {rename_info.uuid}: '{old_path.name}' -> '{new_path.name}'")

                # 1. Rename directory on disk
                if old_path.exists():
                    try:
                        # Ensure parent of new path exists
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                        # os.rename is generally preferred for atomic rename if possible
                        os.rename(old_path, new_path)
                        logger.debug(f"Renamed directory '{old_path}' to '{new_path}'")
                    except OSError as e:
                        logger.error(f'Failed to rename directory for group {rename_info.uuid}: {e}', exc_info=True)
                        # Decide whether to continue trying to update logger
                        continue  # Skip logger update if rename failed
                else:
                    logger.warning(f"Old path '{old_path}' for renamed group {rename_info.uuid} not found on disk.")
                    # Still attempt logger update, as the log might be inconsistent

                # 2. Update logger paths
                try:
                    # Call the refined update_paths method
                    self.dump_tracker.update_paths(old_base_path=old_path, new_base_path=new_path)
                except Exception as e:
                    logger.error(
                        f'Failed to update logger paths for renamed group {rename_info.uuid}: {e}', exc_info=True
                    )

        # --- Handle Modified Groups (Membership changes) ---
        if group_changes.modified:
            group_labels = [group_info.label for group_info in group_changes.modified]
            logger.report(f'Processing {len(group_changes.modified)} modified groups (membership): {group_labels}')
            for mod_info in group_changes.modified:
                # Ensure group path exists (might have been renamed above)
                try:
                    current_group = orm.load_group(uuid=mod_info.uuid)
                    current_group_path_rel = self.dump_paths.get_path_for_group_content(group=current_group)
                    current_group_path_abs = self.dump_paths.base_output_path / current_group_path_rel
                    # Ensure path exists in logger and on disk after potential rename
                    self._register_group_and_prepare_path(current_group, current_group_path_abs)
                    # Pass the *current* absolute path to _update_group_membership
                    self._update_group_membership(mod_info, current_group_path_abs)
                except Exception as e:
                    logger.error(f'Cannot prepare path/update membership for modified group {mod_info.uuid}: {e}')

    def _update_group_membership(self, mod_info: GroupModificationInfo, current_group_path_abs: Path) -> None:
        """Update dump structure for a group with added/removed nodes."""
        # (Make sure this method now receives the correct, potentially *new*, absolute group path)
        msg = (
            f'Updating group membership {mod_info.label}: {len(mod_info.nodes_added)} added, '
            f'{len(mod_info.nodes_removed)} removed.'
        )
        logger.debug(msg)  # Changed level to debug as it's less critical than rename itself

        try:
            group = orm.load_group(uuid=mod_info.uuid)
        except Exception as e:
            logger.error(f'Cannot load group {mod_info.uuid} for membership update: {e}')
            return

        # Node addition handling remains the same - process manager places it correctly
        for node_uuid in mod_info.nodes_added:
            try:
                node = orm.load_node(uuid=node_uuid)
                logger.debug(f"Node {node_uuid} added to group {group.label}. Ensuring it's dumped/linked.")
                # Determine the correct target_path for the node within this group
                # current_group_path_abs is the content root for `group`
                node_target_path_in_group = self.dump_paths.get_path_for_node(
                    node=node,
                    current_content_root=current_group_path_abs,  # This is the new group's content root
                )

                # Pass this explicit target_path to the process manager
                self.process_manager.dump(process_node=node, target_path=node_target_path_in_group)
            except Exception as e:
                logger.warning(f'Could not process node {node_uuid} added to group {group.label}: {e}')

        # Node removal handling uses the passed current_group_path_abs
        if self.config.organize_by_groups and mod_info.nodes_removed:
            logger.debug(f"Handling {len(mod_info.nodes_removed)} nodes removed from group '{group.label}'")
            for node_uuid in mod_info.nodes_removed:
                # Pass the correct current path for cleanup
                self._remove_node_from_group_dir(current_group_path_abs, node_uuid)

    def _remove_node_from_group_dir(self, group_path: Path, node_uuid: str):
        """
        Find and remove a node's dump dir/symlink within a specific group path.
        Handles nodes potentially deleted from the DB by checking filesystem paths.
        """
        node_path_in_logger = self.dump_tracker.get_dump_path_by_uuid(node_uuid)
        # store = self.dump_tracker.get_store_by_uuid(node_uuid)
        if not node_path_in_logger:
            logger.warning(f'Cannot find logger path for node {node_uuid} to remove from group.')
            return

        # Even if node is deleted from DB, we expect the dump_tracker to know the original path name
        node_filename = node_path_in_logger.name

        # Construct potential paths within the group dir where the node might be represented
        # The order matters if duplicates could somehow exist; checks stop on first find.
        possible_paths_to_check = [
            group_path / 'calculations' / node_filename,
            group_path / 'workflows' / node_filename,
            group_path / node_filename,  # Check group root last
        ]

        found_path: Path | None = None
        for potential_path in possible_paths_to_check:
            # Use exists() which works for files, dirs, and symlinks (even broken ones)
            if potential_path.exists():
                found_path = potential_path
                logger.debug(f'Found existing path for node {node_uuid} representation at: {found_path}')
                break  # Stop searching once a potential candidate is found

        if not found_path:
            logger.debug(
                f"Node {node_uuid} representation ('{node_filename}') not found in standard "
                f"group locations within '{group_path.name}'. No removal needed."
            )
            return

        # --- Removal Logic applied to the found_path ---
        try:
            # Determine if the found path IS the original logged path.
            # This is crucial to avoid deleting the source if it was stored directly in the group path.
            is_target_dir = False
            try:
                # Use resolve() for robust comparison, handles symlinks, '.', '..' etc.
                # This comparison is only meaningful if the original logged path *still exists*.
                # If node_path_in_logger points to a non-existent location, found_path cannot be it.
                if node_path_in_logger.exists():
                    # Resolving might fail if permissions are wrong, hence the inner try/except
                    is_target_dir = found_path.resolve() == node_path_in_logger.resolve()
            except OSError as e:
                # Error resolving paths, cannot be certain it's not the target. Err on safe side.
                logger.error(
                    f'Error resolving path {found_path} or {node_path_in_logger}: {e}. '
                    f"Cannot safely determine if it's the target directory. Skipping removal."
                )
                return

            log_suffix = f" from group directory '{group_path.name}'"

            # Proceed with removal based on what found_path is
            if found_path.is_symlink():
                logger.info(f"Removing symlink '{found_path.name}'{log_suffix}.")
                try:
                    # Unlink works even if the symlink target doesn't exist
                    found_path.unlink()
                    # TODO: Remove symlink from logger
                    self.dump_tracker.remove_symlink_from_log_entry(node_uuid, found_path)
                    # store.remove_symlink(found_path)
                except OSError as e:
                    logger.error(f'Failed to remove symlink {found_path}: {e}')

            elif found_path.is_dir() and not is_target_dir:
                # It's a directory *within* the group structure (likely a copy), and NOT the original. Safe to remove.
                logger.info(f"Removing directory '{found_path.name}'{log_suffix}.")
                try:
                    # Ensure safe_delete_dir handles non-empty dirs and potential errors
                    self.dump_paths.safe_delete_directory(directory_path=found_path)
                except Exception as e:
                    logger.error(f'Failed to safely delete directory {found_path}: {e}')

            elif is_target_dir:
                # The path found *is* the primary logged path.
                # Removing the node from a group shouldn't delete its primary data here.
                logger.debug(
                    f'Node {node_uuid} representation found at {found_path} is the primary dump path. '
                    f'It is intentionally not deleted by this operation.'
                )
            else:
                # Exists, but isn't a symlink, and isn't a directory that's safe to remove
                # (e.g., it's a file, or is_target_dir was True but it wasn't a dir?)
                logger.warning(
                    f'Path {found_path} exists but is not a symlink or a directory designated '
                    f'for removal in this context (is_dir={found_path.is_dir()}, is_target_dir={is_target_dir}). '
                    'Skipping removal.'
                )

        except Exception as e:
            # Catch unexpected errors during the removal logic
            logger.exception(
                f'An unexpected error occurred while processing path {found_path} for node {node_uuid}: {e}'
            )
