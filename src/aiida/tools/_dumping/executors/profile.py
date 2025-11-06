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

from pathlib import Path
from typing import TYPE_CHECKING, cast

from aiida import orm
from aiida.common import NotExistent
from aiida.common.log import AIIDA_LOGGER
from aiida.tools._dumping.detect import DumpChangeDetector
from aiida.tools._dumping.executors.collection import CollectionDumpExecutor
from aiida.tools._dumping.tracking import DumpTracker
from aiida.tools._dumping.utils import DumpChanges, DumpPaths, ProcessingQueue

logger = AIIDA_LOGGER.getChild('tools._dumping.executors.profile')

if TYPE_CHECKING:
    from aiida.tools._dumping.config import ProfileDumpConfig
    from aiida.tools._dumping.executors.process import ProcessDumpExecutor
    from aiida.tools._dumping.mapping import GroupNodeMapping
    from aiida.tools._dumping.tracking import DumpTracker


__all__ = ('ProfileDumpExecutor',)


class ProfileDumpExecutor(CollectionDumpExecutor):
    """Strategy for dumping an entire profile."""

    def __init__(
        self,
        config: ProfileDumpConfig,
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
        self.detector: DumpChangeDetector = detector

        # Explicit type hints
        self.dump_paths: DumpPaths
        self.config: ProfileDumpConfig
        self.dump_tracker: DumpTracker
        self.process_dump_executor: ProcessDumpExecutor
        self.current_mapping: GroupNodeMapping

    def dump(self, changes: DumpChanges) -> None:
        """Dumps the entire profile by orchestrating helper methods."""
        if not self.config.all_entries and not self.config.filters_set:
            logger.warning('Default profile dump scope is NONE, skipping profile content dump.')
            return

        # Handle Group Lifecycle (using Group Executor)
        # This applies changes detected earlier (renamed, modified, and membership)
        # Deletion and dumping of new groups handled elsewhere
        self._handle_group_changes(changes.groups)

        # Determine which groups need node processing based on config (e.g., all groups, specific groups)
        groups_to_process = self._determine_groups_to_process()

        # Process nodes within each selected group
        for group in groups_to_process:
            # _process_group handles finding nodes for this group, adding descendants if needed,
            # and calling node_manager.dump_nodes
            group_content_root = self.dump_paths.get_path_for_group(group=group)
            self._process_group(group=group, changes=changes, group_content_path=group_content_root)

        # Process ungrouped nodes if requested by config
        # _dump_ungrouped_nodes finds relevant nodes and calls node_manager.dump_nodes
        if self.config.also_ungrouped:
            self._dump_ungrouped_nodes()

        # Update final stats for logged groups after all dumping is done
        self._update_group_stats()

    def _determine_groups_to_process(self) -> list[orm.Group]:
        """Determine which groups to process based on config."""
        if self.config.all_entries:
            qb_groups = orm.QueryBuilder().append(orm.Group)
            return qb_groups.all(flat=True)

        if not self.config.groups:
            return []

        # Specific groups given as orm entities
        if all(isinstance(g, orm.Group) for g in self.config.groups):
            return cast(list[orm.Group], self.config.groups)

        # Specific groups given via identifier
        try:
            return [orm.load_group(identifier=str(gid)) for gid in self.config.groups]
        except NotExistent as e:
            logger.error(f'Error loading specified group: {e}')
            raise

    def _has_ungrouped_representation(self, node: orm.ProcessNode, ungrouped_path: Path) -> bool:
        """Check if a node already has representation under the ungrouped path.

        :param node: The ``orm.ProcessNode`` to be dumped
        :param ungrouped_path: Path where ungrouped nodes are dumped
        :return: Boolean if node already has been dumped under the ungrouped path
        """
        node_uuid = node.uuid

        try:
            dump_record = self.dump_tracker.get_entry(node_uuid)
        except ValueError as e:
            logger.warning(f'Node {node_uuid} not found in dump tracker: {e}')
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

    def _dump_ungrouped_nodes(self) -> None:
        """Dump ungrouped nodes."""

        # Get filtered ungrouped nodes
        ungrouped_nodes: ProcessingQueue = self.detector._get_ungrouped_nodes()

        # Check against existing representations and dump as needed
        nodes_to_dump = ProcessingQueue()
        ungrouped_path = self.dump_paths.get_path_for_ungrouped_nodes()

        # Process calculations
        for node in ungrouped_nodes.calculations:
            if not self._has_ungrouped_representation(node, ungrouped_path):
                nodes_to_dump.calculations.append(node)

        # Process workflows
        for node in ungrouped_nodes.workflows:
            if not self._has_ungrouped_representation(node, ungrouped_path):
                nodes_to_dump.workflows.append(node)

        if nodes_to_dump.is_empty():
            return

        ungrouped_path.mkdir(exist_ok=True, parents=True)
        (ungrouped_path / DumpPaths.SAFEGUARD_FILE_NAME).touch(exist_ok=True)
        self._dump_nodes(processing_queue=nodes_to_dump, group_context=None)

    def _update_group_stats(self) -> None:
        """Calculate and update final directory stats for all logged groups."""
        for group_uuid, group_log_entry in self.dump_tracker.registries['groups'].entries.items():
            group_path = group_log_entry.path

            if not group_path.is_dir():
                logger.warning(f'Group path {group_path} for UUID {group_uuid} is not a directory. Skipping stats.')
                continue

            group_log_entry.update_stats(group_path)
