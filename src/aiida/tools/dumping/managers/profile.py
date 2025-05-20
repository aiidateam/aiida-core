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

from typing import TYPE_CHECKING, cast

from aiida import orm
from aiida.common import NotExistent
from aiida.common.log import AIIDA_LOGGER
from aiida.orm import Group, QueryBuilder, WorkflowNode
from aiida.tools.dumping.config import GroupDumpScope, ProfileDumpSelection
from aiida.tools.dumping.detect import DumpChangeDetector
from aiida.tools.dumping.logger import DumpLogger
from aiida.tools.dumping.managers.collection import CollectionDumpManager
from aiida.tools.dumping.utils.helpers import DumpChanges, DumpNodeStore
from aiida.tools.dumping.utils.paths import DumpPaths

logger = AIIDA_LOGGER.getChild('tools.dumping.strategies.profile')

if TYPE_CHECKING:
    from aiida.tools.dumping.config import DumpConfig
    from aiida.tools.dumping.logger import DumpLogger
    from aiida.tools.dumping.managers.process import ProcessDumpManager
    from aiida.tools.dumping.mapping import GroupNodeMapping


class ProfileDumpManager(CollectionDumpManager):
    """Strategy for dumping an entire profile."""

    def __init__(
        self,
        config: DumpConfig,
        dump_paths: DumpPaths,
        dump_logger: DumpLogger,
        detector: DumpChangeDetector,
        process_manager: ProcessDumpManager,
        current_mapping: GroupNodeMapping,
    ) -> None:
        super().__init__(
            config=config,
            dump_paths=dump_paths,
            process_manager=process_manager,
            current_mapping=current_mapping,
            dump_logger=dump_logger,
        )
        self.detector = detector

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
            ungrouped_path = self.dump_paths.get_path_for_ungrouped_nodes_root()
            logger.debug(f'Target path for ungrouped nodes: {ungrouped_path}')
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
                            and primary_path.resolve().is_relative_to(ungrouped_path.resolve())
                        ):
                            has_ungrouped_representation = True

                        if not has_ungrouped_representation:
                            for symlink_path in log_entry.symlinks:
                                if symlink_path.exists() and symlink_path.resolve().is_relative_to(
                                    ungrouped_path.resolve()
                                ):
                                    has_ungrouped_representation = True
                                    break
                        if not has_ungrouped_representation:
                            for duplicate_path in log_entry.duplicates:
                                if duplicate_path.exists() and duplicate_path.resolve().is_relative_to(
                                    ungrouped_path.resolve()
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
                ungrouped_path.mkdir(exist_ok=True, parents=True)
                (ungrouped_path / DumpPaths.SAFEGUARD_FILE_NAME).touch(exist_ok=True)
                self._dump_nodes(node_store=nodes_to_dump_ungrouped, group_context=None)
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
                    group_path = self.dump_logger.dump_paths.base_output_path / group_path
                    logger.debug(f'Resolved relative group path for {group_uuid} to {group_path}')
                except Exception as path_e:
                    logger.error(f'Failed to resolve relative path for group {group_uuid}: {path_e}')
                    continue

            if not group_path.is_dir():
                logger.warning(f'Group path {group_path} for UUID {group_uuid} is not a directory. Skipping stats.')
                continue

            logger.debug(f'Calculating stats for group directory: {group_path} (UUID: {group_uuid})')
            try:
                dir_mtime, dir_size = self.dump_paths.get_directory_stats(group_path)
                group_log_entry.dir_mtime = dir_mtime
                group_log_entry.dir_size = dir_size
                logger.debug(f'Updated stats for group {group_uuid}: mtime={dir_mtime}, size={dir_size}')
            except Exception as e:
                logger.error(f'Failed to calculate/update stats for group {group_uuid} at {group_path}: {e}')

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
            group_content_root = self.dump_paths.get_path_for_group_content(
                group=group, parent_group_content_path=None
            )
            self._process_group(group=group, changes=changes, group_content_root_path=group_content_root)

        # 4. Process ungrouped nodes if requested by config
        #    _process_ungrouped_nodes finds relevant nodes and calls node_manager.dump_nodes
        self._process_ungrouped_nodes()

        # 5. Update final stats for logged groups after all dumping is done
        self._update_group_stats()

        logger.info('Finished ProfileDumpManager.')
