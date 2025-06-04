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
from typing import TYPE_CHECKING, cast

from aiida import orm
from aiida.common import NotExistent
from aiida.common.log import AIIDA_LOGGER
from aiida.common.progress_reporter import get_progress_reporter, set_progress_bar_tqdm
from aiida.orm import Group, QueryBuilder, WorkflowNode
from aiida.tools.dumping.config import GroupDumpScope, ProfileDumpSelection
from aiida.tools.dumping.detect import DumpChangeDetector
from aiida.tools.dumping.logger import DumpLog, DumpLogger
from aiida.tools.dumping.utils.helpers import DumpChanges, DumpNodeStore
from aiida.tools.dumping.utils.paths import DumpPaths

logger = AIIDA_LOGGER.getChild('tools.dumping.strategies.profile')

if TYPE_CHECKING:
    from aiida.tools.dumping.config import DumpConfig
    from aiida.tools.dumping.logger import DumpLogger
    from aiida.tools.dumping.managers.process import ProcessDumpManager
    from aiida.tools.dumping.mapping import GroupNodeMapping
    from aiida.tools.dumping.utils.helpers import GroupChanges, GroupModificationInfo


class ProfileDumpManager:
    """Strategy for dumping an entire profile."""

    def __init__(
        self,
        config: DumpConfig,
        dump_paths: DumpPaths,
        dump_logger: DumpLogger,
        detector: DumpChangeDetector,
        process_manager: ProcessDumpManager,
        current_mapping: GroupNodeMapping,
        selected_group: orm.Group | None = None,
    ) -> None:
        self.selected_group = selected_group
        self.config: DumpConfig = config
        self.dump_paths: DumpPaths = dump_paths
        self.process_manager: ProcessDumpManager = process_manager
        self.detector: DumpChangeDetector = detector
        self.current_mapping: GroupNodeMapping = current_mapping
        self.dump_logger: DumpLogger = dump_logger

    def _register_group_and_prepare_path(self, group: orm.Group, group_path: Path) -> None:
        """Ensure group exists in logger and return its path."""

        if group.uuid not in self.dump_logger.groups.entries:
            total_group_path = self.dump_paths.absolute / group_path
            total_group_path.mkdir(exist_ok=True, parents=True)
            (total_group_path / self.dump_paths.safeguard_file).touch()

            msg = f"Registering group '{group.label}' ({group.uuid}) in logger."
            logger.debug(msg)

            group_store = self.dump_logger.groups
            group_store.add_entry(
                uuid=group.uuid,
                entry=DumpLog(path=total_group_path),
            )

    def _determine_groups_to_process(self) -> list[Group]:
        """Determine which groups to process based on config."""
        groups_to_process: list[Group] = []
        if self.config.profile_dump_selection == ProfileDumpSelection.ALL:
            logger.info('Dumping all groups as requested by configuration.')
            try:
                qb_groups = QueryBuilder().append(orm.Group)
                groups_to_process = qb_groups.all(flat=True)
            except Exception as e:
                logger.error(f'Failed to query groups for profile dump: {e}')
                groups_to_process = []
        elif self.config.groups:
            group_identifiers = self.config.groups
            logger.info(f'Dumping specific groups: {group_identifiers}')
            if group_identifiers:
                if isinstance(group_identifiers[0], orm.Group):
                    groups_to_process = cast(list[Group], group_identifiers)
                else:
                    try:
                        groups_to_process = [orm.load_group(identifier=str(gid)) for gid in group_identifiers]
                    except NotExistent as e:
                        logger.error(f'Error loading specified group: {e}. Aborting group processing.')
                    except Exception as e:
                        logger.error(f'Unexpected error loading groups: {e}. Aborting group processing.')
                    # NOTE: Tests failed bc of this
                    # groups_to_process = []  # Ensure it's empty on error
            else:
                logger.warning('Scope set to SPECIFIC but no group identifiers provided.')

        logger.info(f'Will process {len(groups_to_process)} groups found in the profile.')
        return groups_to_process

    def _identify_nodes_for_group(self, group: Group, changes: DumpChanges) -> tuple[DumpNodeStore, list[WorkflowNode]]:
        """Identify nodes explicitly belonging to a given group."""
        nodes_explicitly_in_group = DumpNodeStore()
        group_node_uuids = self.current_mapping.group_to_nodes.get(group.uuid, set())
        workflows_explicitly_in_group: list[WorkflowNode] = []

        for store_key in ['calculations', 'workflows', 'data']:
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

    def _identify_ungrouped_nodes(self, changes: DumpChanges) -> tuple[DumpNodeStore, list[WorkflowNode]]:
        """Identify nodes detected globally that do not belong to any group."""
        ungrouped_nodes_store = DumpNodeStore()
        ungrouped_workflows: list[WorkflowNode] = []

        for store_key in ['calculations', 'workflows', 'data']:
            store_nodes = getattr(changes.nodes.new_or_modified, store_key, [])
            # Node is ungrouped if its UUID is not in the node_to_groups mapping
            ungrouped = [node for node in store_nodes if node.uuid not in self.current_mapping.node_to_groups]
            if ungrouped:
                setattr(ungrouped_nodes_store, store_key, ungrouped)
                if store_key == 'workflows':
                    ungrouped_workflows.extend(
                        cast(
                            list[WorkflowNode],
                            [wf for wf in ungrouped if isinstance(wf, orm.WorkflowNode)],
                        )
                    )
        return ungrouped_nodes_store, ungrouped_workflows

    def _add_ungrouped_descendants_if_needed(
        self,
        ungrouped_nodes_store: DumpNodeStore,
        ungrouped_workflows: list[WorkflowNode],
    ) -> None:
        """Add calculation descendants for ungrouped workflows if config requires."""
        if self.config.only_top_level_calcs or not ungrouped_workflows:
            return

        logger.debug('Finding calculation descendants for ungrouped workflows (only_top_level_calcs=False)')
        try:
            descendants = DumpChangeDetector._get_calculation_descendants(ungrouped_workflows)
            if descendants:
                existing_calc_uuids = {calc.uuid for calc in ungrouped_nodes_store.calculations}
                logged_calc_uuids = set(self.dump_logger.calculations.entries.keys())
                unique_descendants = [
                    desc
                    for desc in descendants
                    if desc.uuid not in existing_calc_uuids and desc.uuid not in logged_calc_uuids
                ]
                if unique_descendants:
                    logger.debug(f'Adding {len(unique_descendants)} unique, unlogged descendants to ungrouped dump.')
                    if not hasattr(ungrouped_nodes_store, 'calculations') or ungrouped_nodes_store.calculations is None:
                        ungrouped_nodes_store.calculations = []
                    ungrouped_nodes_store.calculations.extend(unique_descendants)
                else:
                    logger.debug('All descendants for ungrouped workflows were already included or logged.')
        except Exception as e:
            logger.warning(f'Could not retrieve/process descendants for ungrouped workflows: {e}')

    def _process_ungrouped_nodes(self) -> None:
        """Identify ALL currently ungrouped nodes (ignoring time filter),
        apply necessary filters (like top-level), and ensure they are
        represented in the dump if config.also_ungrouped is True and
        they don't already have an ungrouped representation.
        """
        if not self.config.also_ungrouped:
            logger.info('Skipping ungrouped nodes processing (also_ungrouped=False).')
            return

        logger.info('Processing ungrouped nodes (also_ungrouped=True)...')

        # 1. Determine the target path for ungrouped nodes
        try:
            ungrouped_path_relative = DumpPaths._get_group_path(
                group=None, organize_by_groups=self.config.organize_by_groups
            )
            ungrouped_path_absolute = self.dump_paths.absolute / ungrouped_path_relative
            ungrouped_path_absolute.mkdir(exist_ok=True, parents=True)
            logger.debug(f'Target path for ungrouped nodes: {ungrouped_path_absolute}')
        except Exception as e:
            logger.error(f'Failed to determine or create ungrouped path: {e}', exc_info=True)
            return

        # 2. Use Node Query logic, ignoring time filter, to get initial candidates
        logger.debug('Querying detector for ungrouped nodes with ignore_time_filter=True...')
        try:
            # Ensure self.detector and self.dump_times are accessible
            # Query base Node type to get all potential candidates initially
            initial_ungrouped_nodes: list[orm.Node] = self.detector.node_query._get_nodes(
                orm_type=orm.Node,
                dump_times=self.detector.dump_times,  # Need access to dump_times
                scope=GroupDumpScope.NO_GROUP,
                ignore_time_filter=True,
            )
            logger.debug(
                f'Query returned {len(initial_ungrouped_nodes)} potential ungrouped nodes (ignoring time filter).'
            )
        except AttributeError:
            logger.error('Cannot access detector.node_query or detector.dump_times. Refactoring needed.')
            return
        except Exception as e:
            logger.error(f'Query for ungrouped nodes failed: {e}', exc_info=True)
            return

        # 3. Convert list to dictionary format required by filter methods
        nodes_by_type: dict[str, list[orm.Node]] = {
            'calculations': [],
            'workflows': [],
            'data': [],  # Include data if relevant
        }
        for node in initial_ungrouped_nodes:
            try:
                # Use isinstance for robust type checking
                if isinstance(node, orm.CalculationNode):
                    nodes_by_type['calculations'].append(node)
                elif isinstance(node, orm.WorkflowNode):
                    nodes_by_type['workflows'].append(node)
                # Add elif for orm.Data if needed
                # else: logger.debug(f"Node {node.pk} is not Calc/Work, ignoring for now.")
            except Exception as e:
                logger.warning(f'Error classifying node {node.pk} by type: {e}')

        # 4. Apply the Top-Level Filter (reuse detector's logic)
        logger.debug('Applying top-level filter to ungrouped nodes...')
        try:
            # Pass the dictionary grouped by type to the filter
            filtered_ungrouped_nodes_by_type = self.detector._apply_top_level_filter(nodes_by_type)
            wf_count = len(filtered_ungrouped_nodes_by_type.get('workflows', []))
            calc_count = len(filtered_ungrouped_nodes_by_type.get('calculations', []))
            logger.debug(f'After top-level filter: {wf_count} workflows, {calc_count} calculations remain.')
        except AttributeError:
            logger.error('Cannot access detector._apply_top_level_filter. Refactoring needed.')
            return
        except Exception as e:
            logger.error(f'Applying top-level filter failed: {e}', exc_info=True)
            return

        nodes_to_dump_ungrouped = DumpNodeStore()
        nodes_processed_count = 0

        # 5. Check remaining nodes against logger for existing UNGROUPED representation
        # Iterate through the dictionary returned by the filter
        for store_key, node_list in filtered_ungrouped_nodes_by_type.items():
            if store_key not in ['calculations', 'workflows', 'data']:  # Ensure valid store key
                continue
            for node in node_list:
                node_uuid = node.uuid
                log_entry = self.dump_logger.get_store_by_uuid(node_uuid)

                has_ungrouped_representation = False
                if log_entry:
                    try:
                        primary_path = log_entry.path
                        # Check if primary_path exists before resolving
                        if (
                            primary_path
                            and primary_path.exists()
                            and primary_path.resolve().is_relative_to(ungrouped_path_absolute.resolve())
                        ):
                            has_ungrouped_representation = True

                        if not has_ungrouped_representation:
                            for symlink_path in log_entry.symlinks:
                                if symlink_path.exists() and symlink_path.resolve().is_relative_to(
                                    ungrouped_path_absolute.resolve()
                                ):
                                    has_ungrouped_representation = True
                                    break
                        if not has_ungrouped_representation:
                            for duplicate_path in log_entry.duplicates:
                                if duplicate_path.exists() and duplicate_path.resolve().is_relative_to(
                                    ungrouped_path_absolute.resolve()
                                ):
                                    has_ungrouped_representation = True
                                    break
                    except (OSError, ValueError, AttributeError) as e:
                        logger.warning(f'Error resolving/checking paths for logged node {node_uuid}: {e}')
                    except Exception as e:
                        logger.error(f'Unexpected error checking paths for logged node {node_uuid}: {e}', exc_info=True)

                # 6. Schedule dump if needed
                if not has_ungrouped_representation:
                    msg = (
                        f'Ungrouped node {node_uuid} (passed filters) lacks representation under '
                        "'{ungrouped_path_relative}'. Scheduling."
                    )
                    logger.debug(msg)
                    # Add to the correct list within nodes_to_dump_ungrouped
                    getattr(nodes_to_dump_ungrouped, store_key).append(node)

        # 7. Dump the collected nodes
        if len(nodes_to_dump_ungrouped) > 0:
            logger.report(f'Dumping/linking {len(nodes_to_dump_ungrouped)} nodes under ungrouped path...')
            try:
                (ungrouped_path_absolute / self.dump_paths.safeguard_file).touch(exist_ok=True)
                self._dump_nodes(nodes_to_dump_ungrouped, group=None)
                nodes_processed_count = len(nodes_to_dump_ungrouped)
            except Exception as e:
                logger.error(f'Failed processing nodes under ungrouped path: {e}', exc_info=True)
        else:
            logger.info('No ungrouped nodes required a new representation in the dump after applying filters.')

        logger.info(f'Finished processing ungrouped nodes. Processed {nodes_processed_count} nodes.')

    def _update_group_stats(self) -> None:
        """Calculate and update final directory stats for all logged groups."""
        logger.info('Calculating final directory stats for all registered groups...')
        for group_uuid, group_log_entry in self.dump_logger.groups.entries.items():
            group_path = group_log_entry.path
            if not group_path.is_absolute():
                try:
                    group_path = self.dump_logger.dump_paths.parent / group_path
                    logger.debug(f'Resolved relative group path for {group_uuid} to {group_path}')
                except Exception as path_e:
                    logger.error(f'Failed to resolve relative path for group {group_uuid}: {path_e}')
                    continue

            if not group_path.is_dir():
                logger.warning(f'Group path {group_path} for UUID {group_uuid} is not a directory. Skipping stats.')
                continue

            logger.debug(f'Calculating stats for group directory: {group_path} (UUID: {group_uuid})')
            try:
                dir_mtime, dir_size = DumpPaths._get_directory_stats(group_path)
                group_log_entry.dir_mtime = dir_mtime
                group_log_entry.dir_size = dir_size
                logger.debug(f'Updated stats for group {group_uuid}: mtime={dir_mtime}, size={dir_size}')
            except Exception as e:
                logger.error(f'Failed to calculate/update stats for group {group_uuid} at {group_path}: {e}')

    def _add_and_dump_group_descendants_if_needed(
        self,
        group: Group,
        workflows_in_group: list[WorkflowNode],
    ) -> None:
        """
        Finds calculation descendants for the group's workflows (if config requires)
        and immediately triggers their dump within the group context.
        """
        if self.config.only_top_level_calcs or not workflows_in_group:
            return  # Skip if only dumping top-level or no workflows in group

        msg = (
            'Finding and dumping calculation descendants for workflows in group'
            "'{group.label}' (only_top_level_calcs=False)"
        )
        logger.debug(msg)
        try:
            descendants = DumpChangeDetector._get_calculation_descendants(workflows_in_group)
            if not descendants:
                logger.debug(f"No calculation descendants found for workflows in group '{group.label}'.")
                return

            logged_calc_uuids = set(self.dump_logger.calculations.entries.keys())

            # Identify descendants that are not already logged (dumped previously)
            unique_unlogged_descendants = [desc for desc in descendants if desc.uuid not in logged_calc_uuids]

            if unique_unlogged_descendants:
                msg = (
                    f'Immediately dumping {len(unique_unlogged_descendants)} unique, '
                    "unlogged calculation descendants for group '{group.label}'."
                )
                logger.info(msg)
                # Create a temporary store just for these descendants
                descendant_store = DumpNodeStore(calculations=unique_unlogged_descendants)
                # Call node manager to dump these *now* within the group context
                # This ensures they are created directly under .../calculations/
                self._dump_nodes(descendant_store, group=group)
                # They will now be in the logger before the main workflow dump encounters them nested.
            else:
                logger.debug(f"All descendants for group '{group.label}' were already logged.")
        except Exception as e:
            logger.warning(
                f"Could not retrieve/process/dump descendants for group '{group.label}': {e}",
                exc_info=True,
            )

    def _process_group(self, group: Group, changes: DumpChanges) -> None:
        """Process a single group: find nodes, dump descendants, dump explicit nodes."""
        logger.debug(f'Processing group: {group.label} ({group.uuid})')
        group_path_relative = DumpPaths._get_group_path(group=group, organize_by_groups=self.config.organize_by_groups)
        group_path_absolute = self.dump_paths.absolute / group_path_relative

        try:
            self._register_group_and_prepare_path(
                group=group,
                group_path=group_path_absolute,
            )
        except Exception as e:
            logger.error(f'Failed to handle group path for {group.label}: {e}')
            return

        # 1. Identify nodes explicitly in this group from the global changes
        #    We mainly care about the workflows here for the descendant logic.
        nodes_explicitly_in_group, workflows_in_group = self._identify_nodes_for_group(group, changes)

        # 2. Find and *immediately* dump calculation descendants if required
        #    This ensures the direct dump under ".../calculations/" happens first.
        self._add_and_dump_group_descendants_if_needed(group, workflows_in_group)

        # 3. Dump the nodes explicitly identified for this group
        #    (This will primarily be the workflows now, potentially some top-level calcs)
        #    Filter out calculations already dumped in step 2 to avoid redundant primary dump calls.
        explicit_calcs_in_group = nodes_explicitly_in_group.calculations
        explicit_workflows_in_group = nodes_explicitly_in_group.workflows
        explicit_data_in_group = nodes_explicitly_in_group.data  # Assuming data handling exists

        # Create final store for this step (mainly workflows + maybe top-level calcs/data)
        store_for_explicit_dump = DumpNodeStore(
            calculations=explicit_calcs_in_group,  # Keep explicit calcs if any
            workflows=explicit_workflows_in_group,
            data=explicit_data_in_group,
        )

        if store_for_explicit_dump and len(store_for_explicit_dump) > 0:
            logger.info(f"Dumping {len(store_for_explicit_dump)} explicitly identified nodes for group '{group.label}'")
            try:
                # Dump these nodes (e.g., the Workflow) in the group context
                self._dump_nodes(store_for_explicit_dump, group=group)
                # When the workflow dump recurses, it will find descendants already logged
                # and trigger DUMP_DUPLICATE or SYMLINK correctly.
            except Exception as e:
                logger.error(
                    f"Error dumping explicitly identified nodes for group '{group.label}': {e}",
                    exc_info=True,
                )
        else:
            logger.debug(
                f"No further explicitly identified nodes to dump in group '{group.label}' after handling descendants."
            )

    def _handle_group_changes(self, group_changes: GroupChanges):
        """Handle changes in the group structure since the last dump.

        Apart from membership changes in the group-node mapping, this doesn't do much else actual work, as the actual
        dumping and deleting are handled in other places.

        :param group_changes: _description_
        """
        logger.report('Processing group changes...')

        # 1. Handle Deleted Groups (Directory deletion handled by DeletionManager)
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
                    group_path = DumpPaths._get_group_path(
                        group=group, organize_by_groups=self.config.organize_by_groups
                    )
                    self._register_group_and_prepare_path(
                        group=group,
                        group_path=group_path,
                    )
                    # Dumping nodes within this new group will happen if they
                    # are picked up by the NodeChanges detection based on the config.
                except Exception as e:
                    logger.warning(f'Could not process new group {group_info.uuid}: {e}')

        # --- Handle Renamed Groups ---
        if self.config.update_groups and group_changes.renamed:
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
                    self.dump_logger.update_paths(old_base_path=old_path, new_base_path=new_path)
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
                    current_group_path_rel = DumpPaths._get_group_path(current_group, self.config.organize_by_groups)
                    current_group_path_abs = self.dump_paths.absolute / current_group_path_rel
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
                # Process manager dump will handle placing it under the correct *current* group path
                self.process_manager.dump(process_node=node, group=group)
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
        node_path_in_logger = self.dump_logger.get_dump_path_by_uuid(node_uuid)
        # store = self.dump_logger.get_store_by_uuid(node_uuid)
        if not node_path_in_logger:
            logger.warning(f'Cannot find logger path for node {node_uuid} to remove from group.')
            return

        # Even if node is deleted from DB, we expect the dump_logger to know the original path name
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
                    self.dump_logger.remove_symlink_from_log_entry(node_uuid, found_path)
                    # store.remove_symlink(found_path)
                except OSError as e:
                    logger.error(f'Failed to remove symlink {found_path}: {e}')

            elif found_path.is_dir() and not is_target_dir:
                # It's a directory *within* the group structure (likely a copy), and NOT the original. Safe to remove.
                logger.info(f"Removing directory '{found_path.name}'{log_suffix}.")
                try:
                    # Ensure safe_delete_dir handles non-empty dirs and potential errors
                    DumpPaths._safe_delete_dir(found_path, safeguard_file=DumpPaths.safeguard_file)
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

    def _dump_nodes(self, node_store: DumpNodeStore, group: orm.Group | None = None):
        """Dump a collection of nodes from a node store within an optional group context.

        :param node_store: _description_
        :param group: _description_, defaults to None
        """
        set_progress_bar_tqdm()
        nodes_to_dump = []
        nodes_to_dump.extend(node_store.calculations)
        nodes_to_dump.extend(node_store.workflows)
        if not nodes_to_dump:
            return
        desc = f'Dumping {len(nodes_to_dump)} nodes'
        if group:
            desc += f" for group '{group.label}'"
        logger.report(desc)
        with get_progress_reporter()(desc=desc, total=len(nodes_to_dump)) as progress:
            for node in nodes_to_dump:
                try:
                    # Call the main entry point for dumping a single process
                    self.process_manager.dump(process_node=node, group=group)
                except Exception as e:
                    logger.error(
                        f'Failed preparing/dumping node PK={node.pk}: {e}',
                        exc_info=True,
                    )
                finally:
                    progress.update()

    def dump(self, changes: DumpChanges) -> None:
        """Dumps the entire profile by orchestrating helper methods."""
        logger.info('Executing ProfileDumpManager')
        if self.config.profile_dump_selection == ProfileDumpSelection.NONE:
            logger.report('Default profile dump scope is NONE, skipping profile content dump.')
            return

        # 1. Handle Group Lifecycle (using Group Manager)
        #    This applies changes detected earlier (new/deleted groups, membership)
        #    Directory creation/deletion for groups happens here or in DeletionManager
        logger.info('Processing group lifecycle and membership changes...')
        self._handle_group_changes(changes.groups)

        # 2. Determine which groups need node processing based on config
        #    (e.g., all groups, specific groups)
        groups_to_process = self._determine_groups_to_process()

        # 3. Process nodes within each selected group
        logger.info('Processing nodes within groups...')
        for group in groups_to_process:
            # _process_group handles finding nodes for this group,
            # adding descendants if needed, and calling node_manager.dump_nodes
            self._process_group(group, changes)

        # 4. Process ungrouped nodes if requested by config
        #    _process_ungrouped_nodes finds relevant nodes and calls node_manager.dump_nodes
        self._process_ungrouped_nodes()

        # 5. Update final stats for logged groups after all dumping is done
        self._update_group_stats()

        logger.info('Finished ProfileDumpManager.')
