###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""DumpEngine as top-level orchestrator of dump operations with setup and teardown."""

from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Union

from aiida import orm
from aiida.common import AIIDA_LOGGER
from aiida.manage.configuration.profile import Profile
from aiida.tools.dumping.config import DumpConfig, DumpMode
from aiida.tools.dumping.detect import DumpChangeDetector
from aiida.tools.dumping.executors import DeletionExecutor, GroupDumpExecutor, ProcessDumpExecutor, ProfileDumpExecutor
from aiida.tools.dumping.mapping import GroupNodeMapping
from aiida.tools.dumping.tracking import DumpTracker
from aiida.tools.dumping.utils import DumpChanges, DumpPaths, DumpTimes

logger = AIIDA_LOGGER.getChild('tools.dumping.engine')


class DumpEngine:
    """Engine that orchestrates the dump process including setup and teardown operations."""

    def __init__(
        self,
        dump_target_entity: Union[orm.ProcessNode, orm.Group, Profile],
        base_output_path: Path,
        config: DumpConfig | None = None,
    ):
        """Engine constructor that initializes all entities needed for dumping.

        :param dump_target_entity: AiiDA object that will be dumped
        :param base_output_path: Main dumping output path
        :param config: Populated ``DumpConfig`` instance, defaults to None
        """

        self.config: DumpConfig = config or DumpConfig()
        self.dump_target_entity = dump_target_entity

        self.dump_paths = DumpPaths(
            base_output_path=base_output_path,
            config=self.config,
            dump_target_entity=dump_target_entity,
        )

        # Need to prepare directory here, as if  `overwrite` selected, the tracker instance should be empty
        # by cleaning the previous log file
        self.dump_paths.prepare_directory(path_to_prepare=base_output_path)

        # Load log data, stored mapping, and last dump time string from file
        self.dump_tracker = DumpTracker.load(self.dump_paths)
        self.dump_times = DumpTimes.from_last_log_time(self.dump_tracker._last_dump_time_str)

        # --- Initialize detector for changes ---
        self.detector = DumpChangeDetector(
            dump_tracker=self.dump_tracker, dump_paths=self.dump_paths, config=self.config, dump_times=self.dump_times
        )

    @cached_property
    def current_mapping(self) -> GroupNodeMapping:
        """Build and cache the current group-node mapping from the database.

        This is only computed when needed (for group/profile dumps) and cached for reuse.
        """
        return GroupNodeMapping.build_from_db()

    def _log_dump_start(self) -> None:
        """Log the start of a dump operation."""

        dump_start_report = ''
        if isinstance(self.dump_target_entity, orm.ProcessNode):
            dump_start_report = f'process node (PK: {self.dump_target_entity.pk})'
        elif isinstance(self.dump_target_entity, orm.Group):
            dump_start_report = f'group `{self.dump_target_entity.label}` (PK: {self.dump_target_entity.pk})'
        elif isinstance(self.dump_target_entity, Profile):
            dump_start_report = f'profile `{self.dump_target_entity.name}`'

        msg = f'Starting dump of {dump_start_report} in {self.config.dump_mode.name.lower()} mode.'
        if self.config.dump_mode != DumpMode.DRY_RUN:
            logger.report(msg)

    def dump(self) -> None:
        """Selects and executes the appropriate dump strategy based on the self.dump_target_entity."""

        # Initialize ProcessDumpExecutor as it is needed for all dumping operations
        self.process_dump_executor = ProcessDumpExecutor(
            config=self.config,
            dump_paths=self.dump_paths,
            dump_tracker=self.dump_tracker,
            dump_times=self.dump_times,
        )

        # Log start message
        self._log_dump_start()

        # Call appropriate helper method
        if isinstance(self.dump_target_entity, orm.ProcessNode):
            self._dump_process()
        elif isinstance(self.dump_target_entity, orm.Group):
            self._dump_group()
        elif isinstance(self.dump_target_entity, Profile):
            self._dump_profile()

        # Save final dump log for group and profile dumps (process dumps don't return mapping)
        if isinstance(self.dump_target_entity, (orm.Group, Profile)):
            current_mapping = self.current_mapping
        else:
            current_mapping = None

        logger.report(f'Saving final dump log to file `{DumpPaths.TRACKING_LOG_FILE_NAME}`.')
        self.dump_tracker.save(current_dump_time=self.dump_times.current, group_node_mapping=current_mapping)

    def _dump_process(self) -> None:
        """Dump a single ``orm.ProcessNode``."""

        assert isinstance(self.dump_target_entity, orm.ProcessNode)

        # For a single ProcessNode, its dump root is the base_output_path.
        # ProcessManager uses DumpPaths to place content within this root.
        self.process_dump_executor.dump(
            process_node=self.dump_target_entity, target_path=self.dump_paths.base_output_path
        )
        self.process_dump_executor.readme_generator._generate(self.dump_target_entity, self.dump_paths.base_output_path)

    def _dump_group(self) -> None:
        """Dump a group and its associated nodes."""
        assert isinstance(self.dump_target_entity, orm.Group)
        node_changes = self.detector._detect_node_changes(group=self.dump_target_entity)
        group_changes = self.detector._detect_group_changes(
            previous_mapping=self.dump_tracker.group_node_mapping,
            current_mapping=self.current_mapping,
            specific_group_uuid=self.dump_target_entity.uuid,
        )
        all_changes = DumpChanges(nodes=node_changes, groups=group_changes)

        if self.config.dump_mode == DumpMode.DRY_RUN:
            print(all_changes.to_table())
            return None

        if self.config.delete_missing:
            deletion_manager = DeletionExecutor(
                config=self.config,
                dump_paths=self.dump_paths,
                dump_tracker=self.dump_tracker,
                dump_changes=all_changes,
                previous_mapping=self.dump_tracker.group_node_mapping,
            )
            deletion_manager._handle_deleted_entities()

        # GroupDumpExecutor needs the specific group and the scoped changes.
        # The DumpPaths instance within GroupDumpExecutor will be the same as DumpEngine's.
        group_dump_executor = GroupDumpExecutor(
            group_to_dump=self.dump_target_entity,
            config=self.config,
            dump_paths=self.dump_paths,
            dump_tracker=self.dump_tracker,
            process_dump_executor=self.process_dump_executor,
            current_mapping=self.current_mapping,
        )
        group_dump_executor.dump(changes=all_changes)

    def _dump_profile(self) -> None:
        """Dump a profile and its associated data."""
        assert isinstance(self.dump_target_entity, Profile)

        if not self.config.all_entries and not self.config.filters_set:
            # NOTE: Hack for now, delete empty directory again.
            # Ideally don't even create in the first place.
            # Need to check again where it is actually created.
            self.dump_paths.safe_delete_directory(path=self.dump_paths.base_output_path)
            return None

        node_changes = self.detector._detect_node_changes()
        group_changes = self.detector._detect_group_changes(
            previous_mapping=self.dump_tracker.group_node_mapping, current_mapping=self.current_mapping
        )
        all_changes = DumpChanges(nodes=node_changes, groups=group_changes)

        if all_changes.is_empty():
            logger.report('No changes detected since last dump and not dumping ungrouped. Nothing to do.')
            return None

        if self.config.dump_mode == DumpMode.DRY_RUN:
            print(all_changes.to_table())
            return None

        if self.config.delete_missing:
            deletion_manager = DeletionExecutor(
                config=self.config,
                dump_paths=self.dump_paths,
                dump_tracker=self.dump_tracker,
                dump_changes=all_changes,
                previous_mapping=self.dump_tracker.group_node_mapping,
            )
            deletion_manager._handle_deleted_entities()

        profile_dump_executor = ProfileDumpExecutor(
            config=self.config,
            dump_paths=self.dump_paths,
            dump_tracker=self.dump_tracker,
            process_dump_executor=self.process_dump_executor,
            detector=self.detector,
            current_mapping=self.current_mapping,
        )
        profile_dump_executor.dump(changes=all_changes)
