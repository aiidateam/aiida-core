###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import annotations

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
    """Core engine that orchestrates the dump process."""

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

        self.dump_paths.prepare_directory(path_to_prepare=base_output_path)

        # --- Initialize Times, Logger, and NodeGroupMapping ---
        self.dump_times, self.dump_tracker, self.stored_mapping = self._initialize_times_tracker_and_mapping()

        # --- Initialize detector for changes ---
        self.detector = DumpChangeDetector(
            dump_tracker=self.dump_tracker, dump_paths=self.dump_paths, config=self.config, dump_times=self.dump_times
        )

        # --- Initialize ProcessDumpExecutor ---
        self.process_dump_executor = ProcessDumpExecutor(
            config=self.config,
            dump_paths=self.dump_paths,
            dump_tracker=self.dump_tracker,
            dump_times=self.dump_times,
        )

    def _initialize_times_tracker_and_mapping(
        self,
    ) -> tuple[DumpTimes, DumpTracker, GroupNodeMapping | None]:
        """Initialize dump times, load logger data, and load stored mapping.

        :return: _description_
        """

        # Clear log file if overwriting
        if self.config.dump_mode == DumpMode.OVERWRITE and self.dump_paths.tracking_log_file_path.exists():
            self.dump_paths.tracking_log_file_path.unlink()

        # Load log data, stored mapping, and last dump time string from file
        dump_tracker, stored_mapping = DumpTracker.load(self.dump_paths)
        last_dump_time_str = dump_tracker._last_dump_time_str

        # Initialize DumpTimes based on loaded time string
        dump_times = DumpTimes.from_last_log_time(last_dump_time_str)

        return dump_times, dump_tracker, stored_mapping

    def _log_dump_start(self) -> None:
        """Log the start of a dump operation and validate self.dump_target_entity type."""

        if isinstance(self.dump_target_entity, orm.ProcessNode):
            dump_start_report = f'process node (PK: {self.dump_target_entity.pk})'
        elif isinstance(self.dump_target_entity, orm.Group):
            dump_start_report = f'group `{self.dump_target_entity.label}` (PK: {self.dump_target_entity.pk})'
        elif isinstance(self.dump_target_entity, Profile):
            dump_start_report = f'profile `{self.dump_target_entity.name}`'
        else:
            msg = f'self.dump_target_entity type {type(self.dump_target_entity)} not supported.'
            raise ValueError(msg)

        msg = f'Starting dump of {dump_start_report} in {self.config.dump_mode.name.lower()} mode.'
        if self.config.dump_mode != DumpMode.DRY_RUN:
            logger.report(msg)

    def dump(self) -> None:
        """
        Selects and executes the appropriate dump strategy based on the self.dump_target_entity.
        The base output directory is assumed to be prepared by DumpPaths.__init__().
        """
        # Define mapping from entity types to dump methods
        dump_method_map = [
            (orm.Group, self._dump_group),
            (Profile, self._dump_profile),
            (orm.ProcessNode, self._dump_process),
        ]

        # Log start message
        self._log_dump_start()

        # Execute the appropriate dump strategy by checking isinstance for each type
        dump_method = None
        for entity_type, method in dump_method_map:
            if isinstance(self.dump_target_entity, entity_type):
                dump_method = method
                break

        if dump_method is None:
            msg = f'Entity type {type(self.dump_target_entity)} not supported.'
            raise ValueError(msg)

        dump_method()

        # Save final dump log for group and profile dumps (process dumps don't return mapping)
        if isinstance(self.dump_target_entity, (orm.Group, Profile)):
            # TODO: This is built in multiple places...
            current_mapping = GroupNodeMapping.build_from_db()
        else:
            current_mapping = None
        logger.report(f'Saving final dump log to file `{DumpPaths.TRACKING_LOG_FILE_NAME}`.')
        self.dump_tracker.save(current_dump_time=self.dump_times.current, group_node_mapping=current_mapping)

    def _dump_process(self) -> None:
        """Dump a single process node.

        :param self.dump_target_entity: The process node to dump
        """
        # For a single ProcessNode, its dump root is the base_output_path.
        # ProcessManager uses DumpPaths to place content within this root.
        self.process_dump_executor.dump(
            process_node=self.dump_target_entity, target_path=self.dump_paths.base_output_path
        )
        self.process_dump_executor.readme_generator._generate(self.dump_target_entity, self.dump_paths.base_output_path)

    def _dump_group(self) -> None:
        """Dump a group and its associated nodes.

        :param self.dump_target_entity: The group to dump
        :return: Current mapping of groups to nodes
        """
        node_changes = self.detector._detect_node_changes(group=self.dump_target_entity)
        current_mapping = GroupNodeMapping.build_from_db()
        group_changes = self.detector._detect_group_changes(
            stored_mapping=self.stored_mapping,
            current_mapping=current_mapping,
            specific_group_uuid=self.dump_target_entity.uuid,
        )
        all_changes = DumpChanges(nodes=node_changes, groups=group_changes)

        if self.config.delete_missing:
            deletion_manager = DeletionExecutor(
                config=self.config,
                dump_paths=self.dump_paths,
                dump_tracker=self.dump_tracker,
                dump_changes=all_changes,
                stored_mapping=self.stored_mapping,
            )
            deletion_manager._handle_deleted_entities()

        if self.config.dump_mode == DumpMode.DRY_RUN:
            print(all_changes.to_table())
            return None

        # GroupDumpExecutor needs the specific group and the scoped changes.
        # The DumpPaths instance within GroupDumpExecutor will be the same as DumpEngine's.
        group_dump_executor = GroupDumpExecutor(
            group_to_dump=self.dump_target_entity,
            config=self.config,
            dump_paths=self.dump_paths,
            dump_tracker=self.dump_tracker,
            process_dump_executor=self.process_dump_executor,
            current_mapping=current_mapping,
        )
        group_dump_executor.dump(changes=all_changes)

    def _dump_profile(self) -> None:
        """Dump a profile and its associated data.

        :param self.dump_target_entity: The profile to dump
        :return: Current mapping of groups to nodes, or None if no dump was performed
        """
        if not self.config.all_entries and not self.config.filters_set:
            # NOTE: Hack for now, delete empty directory again. Ideally don't even create in the first place
            # Need to check again where it is actually created...
            self.dump_paths.safe_delete_directory(path=self.dump_paths.base_output_path)
            return None

        node_changes = self.detector._detect_node_changes()
        current_mapping = GroupNodeMapping.build_from_db()
        group_changes = self.detector._detect_group_changes(
            stored_mapping=self.stored_mapping, current_mapping=current_mapping
        )
        all_changes = DumpChanges(nodes=node_changes, groups=group_changes)

        if all_changes.is_empty():
            logger.report('No changes detected since last dump and not dumping ungrouped. Nothing to do.')
            return current_mapping

        if self.config.delete_missing:
            deletion_manager = DeletionExecutor(
                config=self.config,
                dump_paths=self.dump_paths,
                dump_tracker=self.dump_tracker,
                dump_changes=all_changes,
                stored_mapping=self.stored_mapping,
            )
            deletion_manager._handle_deleted_entities()

        if self.config.dump_mode == DumpMode.DRY_RUN:
            print(all_changes.to_table())
            return current_mapping

        profile_dump_executor = ProfileDumpExecutor(
            config=self.config,
            dump_paths=self.dump_paths,
            dump_tracker=self.dump_tracker,
            process_dump_executor=self.process_dump_executor,
            detector=self.detector,
            current_mapping=current_mapping,
        )
        profile_dump_executor.dump(changes=all_changes)
