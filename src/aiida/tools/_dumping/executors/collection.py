###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Common functionality for the GroupDumpExecutor and ProfileDumpExecutor."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from aiida import orm
from aiida.common import AIIDA_LOGGER, NotExistent
from aiida.common.progress_reporter import get_progress_reporter, set_progress_bar_tqdm
from aiida.tools._dumping.detect import DumpChangeDetector
from aiida.tools._dumping.tracking import DumpRecord, DumpTracker
from aiida.tools._dumping.utils import DumpChanges, DumpPaths, ProcessingQueue

if TYPE_CHECKING:
    from aiida.tools._dumping.config import GroupDumpConfig, ProfileDumpConfig
    from aiida.tools._dumping.executors.process import ProcessDumpExecutor
    from aiida.tools._dumping.mapping import GroupNodeMapping
    from aiida.tools._dumping.utils import GroupChanges, GroupModificationInfo

logger = AIIDA_LOGGER.getChild('tools._dumping.executors.collection')


class CollectionDumpExecutor:
    def __init__(
        self,
        config: Union[GroupDumpConfig, ProfileDumpConfig],
        dump_paths: DumpPaths,
        dump_tracker: DumpTracker,
        process_dump_executor: ProcessDumpExecutor,
        current_mapping: GroupNodeMapping,
    ) -> None:
        self.config: Union[GroupDumpConfig, ProfileDumpConfig] = config
        self.dump_paths: DumpPaths = dump_paths
        self.process_dump_executor: ProcessDumpExecutor = process_dump_executor
        self.dump_tracker: DumpTracker = dump_tracker
        self.current_mapping: GroupNodeMapping = current_mapping

    def _register_group_and_prepare_path(self, group: orm.Group, group_content_path: Path) -> None:
        """Ensures the group's specific content directory is prepared and the group is logged.

        :param group: The passed group
        :param group_content_path: The top-level dumping path for the group
        """

        self.dump_paths._prepare_directory(group_content_path, is_leaf_node_dir=False)

        if group.uuid not in self.dump_tracker.registries['groups'].entries:
            self.dump_tracker.registries['groups'].add_entry(
                uuid=group.uuid,
                entry=DumpRecord(path=group_content_path),
            )

    def _identify_nodes_in_group(self, group: orm.Group, changes: DumpChanges) -> ProcessingQueue:
        """Identifies nodes explicitly belonging to a given group from the provided changes.

        :param group: The specific group
        :param changes: Populated ``DumpChanges`` object with all changes since the last dump
        :return: ProcessingQueue containing nodes that belong to this group
        """

        nodes_explicitly_in_group = ProcessingQueue()
        group_node_uuids = [node.uuid for node in group.nodes]

        calc_nodes = [n for n in changes.nodes.new_or_modified.calculations if n.uuid in group_node_uuids]
        workflow_nodes = [n for n in changes.nodes.new_or_modified.workflows if n.uuid in group_node_uuids]

        if calc_nodes:
            nodes_explicitly_in_group.calculations = calc_nodes
        if workflow_nodes:
            nodes_explicitly_in_group.workflows = workflow_nodes

        return nodes_explicitly_in_group

    def _dump_group_descendant_calcs(
        self,
        group: orm.Group,
        nodes_in_group: ProcessingQueue,
        group_root_path: Path,
    ) -> None:
        """Finds and dumps calculation descendants for the group's workflows

        :param group: The specific group
        :param nodes_in_group: ProcessingQueue containing the calcs and workflows in the group
        :param group_root_path: _description_
        """

        workflows_in_group = [wf for wf in nodes_in_group.workflows if isinstance(wf, orm.WorkflowNode)]

        if not workflows_in_group:
            return

        descendants = DumpChangeDetector.get_calculation_descendants(workflows_in_group)
        if not descendants:
            return

        logged_calc_uuids = set(self.dump_tracker.registries['calculations'].entries.keys())
        unique_unlogged_descendants = [desc for desc in descendants if desc.uuid not in logged_calc_uuids]

        if not unique_unlogged_descendants:
            return

        # Descendants are dumped with the group context, into the group's content root.
        descendant_queue = ProcessingQueue(calculations=unique_unlogged_descendants)
        self._dump_nodes(
            processing_queue=descendant_queue,
            group_context=group,
            current_dump_root_for_nodes=group_root_path,
        )

    def _dump_nodes(
        self,
        processing_queue: ProcessingQueue,
        group_context: Optional[orm.Group] = None,
        current_dump_root_for_nodes: Optional[Path] = None,
    ):
        """Dumps a collection of nodes. Nodes are placed relative to 'current_dump_root_for_nodes'.

        :param processing_queue: _description_
        :param group_context: _description_, defaults to None
        :param current_dump_root_for_nodes: _description_, defaults to None
        """
        set_progress_bar_tqdm()
        nodes_to_dump = []
        nodes_to_dump.extend(processing_queue.calculations)
        nodes_to_dump.extend(processing_queue.workflows)
        if not nodes_to_dump:
            return

        desc = f'Dumping {len(nodes_to_dump)} nodes'
        if group_context:
            desc += f" for group '{group_context.label}'"
        logger.report(desc)

        if current_dump_root_for_nodes is None:
            # This is a fallback, the caller should ideally always provide the explicit root.
            if group_context:
                current_dump_root_for_nodes = self.dump_paths.get_path_for_group(group_context)
            else:  # Ungrouped nodes
                current_dump_root_for_nodes = self.dump_paths.get_path_for_ungrouped_nodes()
            logger.warning(f'current_dump_root_for_nodes was None, derived as: {current_dump_root_for_nodes}')

        with get_progress_reporter()(desc=desc, total=len(nodes_to_dump)) as progress:
            for node in nodes_to_dump:
                # Determine the specific, absolute path for this node's dump directory
                node_specific_dump_path = self.dump_paths.get_path_for_node(
                    node=node,
                    current_content_root=current_dump_root_for_nodes,
                )
                # ProcessDumpExecutor.dump takes the final, specific path for the node.
                self.process_dump_executor.dump(
                    process_node=node,
                    output_path=node_specific_dump_path,
                )
                progress.update()

    def _process_group(self, group: orm.Group, changes: DumpChanges, group_content_path: Path) -> None:
        """
        Process a single group: find its nodes, dump explicit nodes, dump descendants,
        all operating within the provided 'group_content_root_path'.

        :param group: The orm.Group to process.
        :param changes: DumpChanges object
        :param group_content_root_path: The absolute filesystem path where this group's
            direct content (safeguard, type subdirs) should reside.
        """

        # Ensure the group's own content directory is prepared and logged.
        self._register_group_and_prepare_path(group=group, group_content_path=group_content_path)

        # Identify nodes explicitly in this group from the scoped changes.
        nodes_explicitly_in_group = self._identify_nodes_in_group(group, changes)

        # Dump the nodes explicitly identified for this group.
        store_for_explicit_dump = ProcessingQueue(
            calculations=nodes_explicitly_in_group.calculations,
            workflows=nodes_explicitly_in_group.workflows,
        )

        if len(store_for_explicit_dump) == 0:
            return

        # These nodes are dumped into the group_content_path.
        self._dump_nodes(
            processing_queue=store_for_explicit_dump,
            group_context=group,
            current_dump_root_for_nodes=group_content_path,
        )

        # Find and dump calculation descendants if required.
        if not self.config.only_top_level_calcs:
            self._dump_group_descendant_calcs(
                group=group, nodes_in_group=nodes_explicitly_in_group, group_root_path=group_content_path
            )

        # Update stats for this specific group.
        record = self.dump_tracker.get_entry(group.uuid)
        record.update_stats(group_content_path)

    def _handle_group_changes(self, group_changes: GroupChanges) -> None:
        """Handle changes in the group structure since the last dump.

        :param group_changes: Populated ``GroupChanges`` object
        """
        logger.report('Processing group changes...')

        # Handle Deleted Groups. Actual directory deletion handled by DeletionExecutor, only logging done here.
        if group_changes.deleted:
            group_labels = [group_info.label for group_info in group_changes.deleted]
            msg = f'Detected {len(group_changes.deleted)} deleted groups.'
            logger.report(msg)

        # Handle Renamed Groups
        if self.config.relabel_groups and group_changes.renamed:
            logger.report(f'Processing {len(group_changes.renamed)} renamed groups.')
            for rename_info in group_changes.renamed:
                old_path = rename_info.old_path
                new_path = rename_info.new_path

                # Rename directory on disk
                if old_path.exists():
                    try:
                        if not old_path.is_dir():
                            raise OSError(f'Source path {old_path} is not a directory')

                        # Check if new_path already exists (os.rename would fail)
                        if new_path.exists():
                            raise OSError(f'Destination path {new_path} already exists')

                        # Only create parent directory right before rename
                        new_path.parent.mkdir(parents=True, exist_ok=True)

                        # Atomic rename operation
                        os.rename(old_path, new_path)

                        # Only update tracker if rename succeeded
                        self.dump_tracker.update_paths(old_base_path=old_path, new_base_path=new_path)

                    except OSError as e:
                        # Clean up the parent directory if we created it and it's empty
                        if new_path.parent.exists() and not any(new_path.parent.iterdir()):
                            try:
                                new_path.parent.rmdir()
                            except OSError:
                                pass  # Ignore cleanup errors

                        logger.error(f'Failed to rename directory for group {rename_info.uuid}: {e}', exc_info=True)
                        raise

        # Handle Modified Groups (Membership changes)
        if group_changes.modified:
            group_labels = [group_info.label for group_info in group_changes.modified]
            logger.report(f'Processing {len(group_changes.modified)} modified groups (membership): {group_labels}')
            for mod_info in group_changes.modified:
                # Ensure group path exists (might have been renamed above)
                current_group = orm.load_group(uuid=mod_info.uuid)
                current_group_path_rel = self.dump_paths.get_path_for_group(group=current_group)
                current_group_path_abs = self.dump_paths.base_output_path / current_group_path_rel
                # Ensure path exists in logger and on disk after potential rename
                self._register_group_and_prepare_path(current_group, current_group_path_abs)
                # Pass the *current* absolute path to _update_group_membership
                self._update_group_membership(mod_info, current_group_path_abs)

    def _update_group_membership(self, mod_info: GroupModificationInfo, current_group_path_abs: Path) -> None:
        """Update dump structure for a group with added/removed nodes.

        :param mod_info: Populated ``GroupModificationInfo`` instance
        :param current_group_path_abs: Current absolute path of the group.
        """

        # Node addition handling remains the same - process manager places it correctly
        for node_uuid in mod_info.nodes_added:
            try:
                node = orm.load_node(uuid=node_uuid)
            except (ValueError, NotExistent):
                continue

            if not isinstance(node, orm.ProcessNode):
                continue

            # Determine the correct output_path for the node within this group
            # current_group_path_abs is the content root for `group`
            node_output_path_in_group = self.dump_paths.get_path_for_node(
                node=node,
                current_content_root=current_group_path_abs,
            )

            # Pass this explicit output_path to the ProcessDumpExecutor
            self.process_dump_executor.dump(process_node=node, output_path=node_output_path_in_group)

        # Node removal handling uses the passed current_group_path_abs
        if self.config.organize_by_groups and mod_info.nodes_removed:
            for node_uuid in mod_info.nodes_removed:
                # Pass the correct current path for cleanup
                self._remove_node_from_group_dir(current_group_path_abs, node_uuid)

    def _remove_node_from_group_dir(self, group_path: Path, node_uuid: str):
        """Find and remove a node's dump dir/symlink within a specific group path.

        Handles nodes potentially deleted from the DB by checking filesystem paths.

        :param group_path: Current root path of the group
        :param node_uuid: UUID of node that was deleted
        """
        dump_record = self.dump_tracker.get_entry(node_uuid)

        # Even if node is deleted from DB, we expect the dump_tracker to know the original path name
        node_path = dump_record.path
        node_filename = dump_record.path.name

        # Construct potential paths within the group dir where the node might be represented
        # The order matters if duplicates could somehow exist; checks stop on first find.
        paths_to_check = [
            group_path / 'calculations' / node_filename,
            group_path / 'workflows' / node_filename,
            group_path / node_filename,  # Check group root last
        ]

        found_path: Path | None = None
        for potential_path in paths_to_check:
            # exists() works for files, dirs, and symlinks (even broken ones)
            if potential_path.exists():
                found_path = potential_path
                break

        if not found_path:
            return

        # Removal Logic applied to the found_path
        # Determine if the found path IS the original logged path.
        # This is crucial to avoid deleting the source if it was stored directly in the group path.
        is_target_dir = False
        try:
            # This comparison is only meaningful if the original logged path *still exists*.
            # If node_path_in_logger points to a non-existent location, found_path cannot be it.
            if node_path.exists():
                # Resolving might fail if permissions are wrong, hence the inner try/except
                is_target_dir = found_path.resolve() == node_path.resolve()
        except OSError as e:
            # Error resolving paths, cannot be certain it's not the target. Err on safe side.
            logger.error(
                f'Error resolving path {found_path} or {dump_record}: {e}. '
                f"Cannot safely determine if it's the target directory. Skipping removal."
            )
            return

        # Proceed with removal based on what found_path is
        if found_path.is_symlink():
            try:
                # Unlink works even if the symlink target doesn't exist
                found_path.unlink()

                # Remove symlink reference from log entry
                entry = self.dump_tracker.get_entry(node_uuid)
                entry.remove_symlink(found_path)

            except OSError as e:
                logger.error(f'Failed to remove symlink {found_path}: {e}')
            except ValueError:
                raise

        elif found_path.is_dir() and not is_target_dir:
            # It's a directory *within* the group structure (likely a copy), and NOT the original. Safe to remove.
            DumpPaths._safe_delete_directory(path=found_path)
            # Remove duplicate reference from log entry
            try:
                entry = self.dump_tracker.get_entry(node_uuid)
                entry.remove_duplicate(found_path)
            except ValueError:
                raise

        elif is_target_dir:
            # The path found *is* the primary logged path.
            # Removing the node from a group shouldn't delete its primary data here.
            pass
        else:
            # Exists, but isn't a symlink, and isn't a directory that's safe to remove
            logger.warning(
                f'Path {found_path} exists but is not a symlink or a directory designated '
                f'for removal in this context. Skipping removal.'
            )
