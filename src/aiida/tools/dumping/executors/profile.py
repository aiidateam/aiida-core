###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Executor that orchestrates dumping an AiiDA profile."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, cast

from aiida import orm
from aiida.common import NotExistent
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.detect import DumpChangeDetector
from aiida.tools.dumping.executors.collection import CollectionDumpExecutor
from aiida.tools.dumping.tracking import DumpTracker
from aiida.tools.dumping.utils import DumpChanges, DumpNodeStore, DumpPaths

logger = AIIDA_LOGGER.getChild('tools.dumping.executors.profile')

if TYPE_CHECKING:
    from aiida.tools.dumping.config import DumpConfig
    from aiida.tools.dumping.executors.process import ProcessDumpExecutor
    from aiida.tools.dumping.mapping import GroupNodeMapping
    from aiida.tools.dumping.tracking import DumpTracker


class ProfileDumpExecutor(CollectionDumpExecutor):
    """Strategy for dumping an entire profile."""

    def __init__(
        self,
        config: DumpConfig,
        dump_paths: DumpPaths,
        dump_tracker: DumpTracker,
        detector: DumpChangeDetector,
        process_dump_executor: ProcessDumpExecutor,
        current_mapping: GroupNodeMapping,
    ) -> None:
        super().__init__(
            config=config,
            dump_paths=dump_paths,
            process_dump_executor=process_dump_executor,
            current_mapping=current_mapping,
            dump_tracker=dump_tracker,
        )
        self.detector = detector

    def _determine_groups_to_process(self) -> list[orm.Group]:
        """Determine which groups to process based on config."""
        groups_to_process: list[orm.Group] = []
        if not self.config.groups or self.config.all_entries:
            logger.info('Dumping all groups as requested by configuration.')
            qb_groups = orm.QueryBuilder().append(orm.Group)
            groups_to_process = cast(List[orm.Group], qb_groups.all(flat=True))
        elif self.config.groups:
            group_identifiers = self.config.groups
            logger.info(f'Dumping specific groups: {group_identifiers}')
            if group_identifiers:
                if isinstance(group_identifiers[0], orm.Group):
                    groups_to_process = cast(list[orm.Group], group_identifiers)
                else:
                    try:
                        groups_to_process = [orm.load_group(identifier=str(gid)) for gid in group_identifiers]
                    except NotExistent as e:
                        logger.error(f'Error loading specified group: {e}. Aborting group processing.')
            else:
                logger.warning('Scope set to SPECIFIC but no group identifiers provided.')

        logger.info(f'Will process {len(groups_to_process)} groups found in the profile.')
        return groups_to_process

    # TODO: Move to DumpChangeDetector???
    def _identify_ungrouped_nodes(self, changes: DumpChanges) -> tuple[DumpNodeStore, list[orm.WorkflowNode]]:
        """Identify nodes detected globally that do not belong to any group."""

        ungrouped_nodes_store = DumpNodeStore()
        ungrouped_workflows: list[orm.WorkflowNode] = []

        for registry_key in ['calculations', 'workflows']:
            store_nodes = getattr(changes.nodes.new_or_modified, registry_key, [])
            # Node is ungrouped if its UUID is not in the node_to_groups mapping
            ungrouped = [node for node in store_nodes if node.uuid not in self.current_mapping.node_to_groups]
            if ungrouped:
                setattr(ungrouped_nodes_store, registry_key, ungrouped)
                if registry_key == 'workflows':
                    ungrouped_workflows.extend(
                        cast(
                            list[orm.WorkflowNode],
                            [wf for wf in ungrouped if isinstance(wf, orm.WorkflowNode)],
                        )
                    )
        return ungrouped_nodes_store, ungrouped_workflows

    def _add_ungrouped_descendants(
        self,
        ungrouped_nodes_store: DumpNodeStore,
        ungrouped_workflows: list[orm.WorkflowNode],
    ) -> None:
        """Add calculation descendants for ungrouped workflows if config requires."""
        if self.config.only_top_level_calcs or not ungrouped_workflows:
            return

        logger.debug('Finding calculation descendants for ungrouped workflows (only_top_level_calcs=False)')
        descendants = DumpChangeDetector.get_calculation_descendants(ungrouped_workflows)
        if descendants:
            existing_calc_uuids = {calc.uuid for calc in ungrouped_nodes_store.calculations}
            logged_calc_uuids = set(self.dump_tracker.registries['calculations'].entries.keys())
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

    def _has_ungrouped_representation(self, node: orm.ProcessNode, ungrouped_path) -> bool:
        """Check if a node already has representation under the ungrouped path."""
        node_uuid = node.uuid
        dump_record = self.dump_tracker.get_entry(node_uuid)

        if not dump_record:
            return False

        try:
            # Check primary path
            primary_path = dump_record.path
            if primary_path.exists() and primary_path.resolve().is_relative_to(ungrouped_path.resolve()):
                return True

            # Check symlinks
            for symlink_path in dump_record.symlinks:
                if symlink_path.exists() and symlink_path.resolve().is_relative_to(ungrouped_path.resolve()):
                    return True

            # Check duplicates
            for duplicate_path in dump_record.duplicates:
                if duplicate_path.exists() and duplicate_path.resolve().is_relative_to(ungrouped_path.resolve()):
                    return True

        except (OSError, ValueError, AttributeError) as e:
            logger.warning(f'Error resolving/checking paths for logged node {node_uuid}: {e}')

        return False

    def _process_ungrouped_nodes(self) -> None:
        """Process ungrouped nodes for dumping."""
        if not self.config.also_ungrouped:
            logger.info('Skipping ungrouped nodes processing (also_ungrouped=False).')
            return

        # Get filtered ungrouped nodes (includes top-level filtering)
        ungrouped_nodes = self.detector.get_ungrouped_nodes()

        # Check against existing representations and dump as needed
        nodes_to_dump = DumpNodeStore()
        ungrouped_path = self.dump_paths.get_path_for_ungrouped_nodes()

        for store_attr in ['calculations', 'workflows']:
            for node in getattr(ungrouped_nodes, store_attr):
                if not self._has_ungrouped_representation(node, ungrouped_path):
                    getattr(nodes_to_dump, store_attr).append(node)

        if len(nodes_to_dump) > 0:
            logger.report(f'Dumping/linking {len(nodes_to_dump)} nodes under ungrouped path...')
            ungrouped_path.mkdir(exist_ok=True, parents=True)
            (ungrouped_path / DumpPaths.SAFEGUARD_FILE_NAME).touch(exist_ok=True)
            self._dump_nodes(node_store=nodes_to_dump, group_context=None)

    def _update_group_stats(self) -> None:
        """Calculate and update final directory stats for all logged groups."""
        logger.info('Calculating final directory stats for all registered groups...')
        for group_uuid, group_log_entry in self.dump_tracker.registries['groups'].entries.items():
            group_path = group_log_entry.path
            if not group_path.is_absolute():
                group_path = self.dump_paths.base_output_path / group_path
                logger.debug(f'Resolved relative group path for {group_uuid} to {group_path}')

            if not group_path.is_dir():
                logger.warning(f'Group path {group_path} for UUID {group_uuid} is not a directory. Skipping stats.')
                continue

            logger.debug(f'Calculating stats for group directory: {group_path} (UUID: {group_uuid})')
            dir_mtime, dir_size = self.dump_paths.get_directory_stats(group_path)
            group_log_entry.dir_mtime = dir_mtime
            group_log_entry.dir_size = dir_size
            logger.debug(f'Updated stats for group {group_uuid}: mtime={dir_mtime}, size={dir_size}')

    def dump(self, changes: DumpChanges) -> None:
        """Dumps the entire profile by orchestrating helper methods."""
        logger.info('Executing ProfileDumpExecutor')
        if not self.config.all_entries and not self.config.filters_set:
            logger.report('Default profile dump scope is NONE, skipping profile content dump.')
            return

        # 1. Handle Group Lifecycle (using Group Executor)
        #    This applies changes detected earlier (new/deleted groups, membership)
        #    Directory creation/deletion for groups happens here or in DeletionExecutor
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
            group_content_root = self.dump_paths.get_path_for_group(group=group, parent_group_content_path=None)
            self._process_group(group=group, changes=changes, group_content_root_path=group_content_root)

        # 4. Process ungrouped nodes if requested by config
        #    _process_ungrouped_nodes finds relevant nodes and calls node_manager.dump_nodes
        self._process_ungrouped_nodes()

        # 5. Update final stats for logged groups after all dumping is done
        self._update_group_stats()
