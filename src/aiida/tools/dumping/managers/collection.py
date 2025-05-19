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
from aiida.common.log import AIIDA_LOGGER
from aiida.common.progress_reporter import get_progress_reporter, set_progress_bar_tqdm
from aiida.orm import Group, WorkflowNode
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
    from aiida.tools.dumping.utils.helpers import GroupChanges


class CollectionDumpManager:

    def __init__(
        self,
        config: DumpConfig,
        dump_paths: DumpPaths,
        dump_logger: DumpLogger,
        detector: DumpChangeDetector,
        process_manager: ProcessDumpManager,
        current_mapping: GroupNodeMapping,
    ) -> None:
        self.config: DumpConfig = config
        self.dump_paths: DumpPaths = dump_paths
        self.process_manager: ProcessDumpManager = process_manager
        self.detector: DumpChangeDetector = detector
        self.current_mapping: GroupNodeMapping = current_mapping
        self.dump_logger: DumpLogger = dump_logger

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
