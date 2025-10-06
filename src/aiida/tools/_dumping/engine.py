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

from pathlib import Path
from typing import Union

from aiida import orm
from aiida.common import AIIDA_LOGGER
from aiida.manage.configuration.profile import Profile
from aiida.tools._dumping.config import DumpMode, GroupDumpConfig, ProcessDumpConfig, ProfileDumpConfig
from aiida.tools._dumping.detect import DumpChangeDetector
from aiida.tools._dumping.executors import (
    DeletionExecutor,
    GroupDumpExecutor,
    ProcessDumpExecutor,
    ProfileDumpExecutor,
)
from aiida.tools._dumping.mapping import GroupNodeMapping
from aiida.tools._dumping.tracking import DumpTracker
from aiida.tools._dumping.utils import DumpChanges, DumpPaths

logger = AIIDA_LOGGER.getChild('tools._dumping.engine')


class DumpEngine:
    """Engine that orchestrates the dump process including setup and teardown operations."""

    def __init__(
        self,
        dump_target_entity: Union[orm.ProcessNode, orm.Group, Profile],
        base_output_path: Path,
        config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig],
    ):
        """Engine constructor that initializes all entities needed for dumping.

        :param dump_target_entity: AiiDA object that will be dumped
        :param base_output_path: Main dumping output path
        :param config: Populated config instance, defaults to None
        """

        self.config: Union[ProcessDumpConfig, GroupDumpConfig, ProfileDumpConfig] = config
        self.dump_target_entity = dump_target_entity

        self.dump_paths = DumpPaths(
            base_output_path=base_output_path,
            config=self.config,
            dump_target_entity=dump_target_entity,
        )

        # Need to prepare directory here, as if  `overwrite` selected, the tracker instance should be empty
        # by cleaning the previous log file
        self.dump_paths._prepare_directory(path_to_prepare=base_output_path, is_leaf_node_dir=True)

        # Load log data, stored mapping, and dump times from file
        self.dump_tracker = DumpTracker.load(self.dump_paths)
        self.dump_times = self.dump_tracker.dump_times

        # Create the group-node mapping required for the dump from AiiDA's DB depending on the dump target entity
        self.current_mapping = self._build_mapping_for_target()

        # Initialize ProcessDumpExecutor as it is needed for all dumping operations
        self.process_dump_executor = ProcessDumpExecutor(
            config=self.config,
            dump_paths=self.dump_paths,
            dump_tracker=self.dump_tracker,
            dump_times=self.dump_times,
        )

    def _build_mapping_for_target(self) -> GroupNodeMapping:
        """Build the appropriate group-node mapping based on the target entity and config."""
        if isinstance(self.dump_target_entity, orm.Group):
            logger.report(f'Building group-node mapping for single group: <{self.dump_target_entity.label}> ...')
            return GroupNodeMapping.build_from_db(groups=[self.dump_target_entity])

        elif isinstance(self.dump_target_entity, Profile):
            # Profile dump - depends on config
            assert isinstance(self.config, ProfileDumpConfig)

            if self.config.all_entries:
                logger.report('Building group-node mapping for all groups in profile...')
                return GroupNodeMapping.build_from_db(groups=None)
            elif self.config.groups:
                logger.report(f'Building group-node mapping for {len(self.config.groups)} specified groups...')
                return GroupNodeMapping.build_from_db(groups=self.config.groups)
            else:
                return GroupNodeMapping()

        else:
            return GroupNodeMapping()

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

        # Log start message
        self._log_dump_start()

        # Call appropriate helper method
        if isinstance(self.dump_target_entity, orm.ProcessNode):
            self._dump_process()
        elif isinstance(self.dump_target_entity, orm.Group):
            self._dump_group()
        elif isinstance(self.dump_target_entity, Profile):
            self._dump_profile()

        if not self.config.dump_mode == DumpMode.DRY_RUN:
            logger.report(f'Saving final dump log to file `{DumpPaths.TRACKING_LOG_FILE_NAME}`.')
            self.dump_tracker.save()

    def _dump_process(self) -> None:
        """Dump a single ``orm.ProcessNode``."""

        assert isinstance(self.dump_target_entity, orm.ProcessNode)
        assert isinstance(self.config, ProcessDumpConfig)

        # For a single ProcessNode, its dump root is the base_output_path.
        # ProcessManager uses DumpPaths to place content within this root.
        self.process_dump_executor.dump(
            process_node=self.dump_target_entity, output_path=self.dump_paths.base_output_path
        )

        # Readme generation done by the engine rather than executor, as the file should only created for the primary
        # process for `verdi process dump`, not sup-processes, or processes as part of a group/profile dump
        if not self.config.dump_mode == DumpMode.DRY_RUN:
            self.process_dump_executor.readme_generator._generate(
                self.dump_target_entity, self.dump_paths.base_output_path
            )

    def _dump_group(self) -> None:
        """Dump a group and its associated nodes."""

        assert isinstance(self.dump_target_entity, orm.Group)
        assert isinstance(self.config, GroupDumpConfig)

        self.detector = DumpChangeDetector(
            dump_tracker=self.dump_tracker,
            dump_paths=self.dump_paths,
            config=self.config,
            dump_times=self.dump_times,
            current_mapping=self.current_mapping,
        )

        self.dump_tracker.set_current_mapping(self.current_mapping)
        node_changes = self.detector._detect_node_changes(group=self.dump_target_entity)

        group_changes = self.detector._detect_group_changes(
            previous_mapping=self.dump_tracker.previous_mapping,
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
                previous_mapping=self.dump_tracker.previous_mapping,
            )
            deletion_manager._handle_deleted_entities()

        # GroupDumpExecutor needs the specific group and the scoped changes.
        # The DumpPaths instance within GroupDumpExecutor will be the same as DumpEngine's.
        group_dump_executor = GroupDumpExecutor(
            group=self.dump_target_entity,
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
        assert isinstance(self.config, ProfileDumpConfig)

        self.detector = DumpChangeDetector(
            dump_tracker=self.dump_tracker,
            dump_paths=self.dump_paths,
            config=self.config,
            dump_times=self.dump_times,
            current_mapping=self.current_mapping,
        )

        if (
            not self.config.all_entries
            and not self.config.filters_set
            and not self.config.dump_mode == DumpMode.DRY_RUN
        ):
            # NOTE: Hack for now, delete empty directory again.
            # Ideally don't even create in the first place.
            # Need to check again where it is actually created.
            DumpPaths._safe_delete_directory(path=self.dump_paths.base_output_path)
            return None

        self.dump_tracker.set_current_mapping(self.current_mapping)

        logger.report('Detecting changes since last dump. This may take a while for large databases...')
        logger.report('Detecting node changes...')
        node_changes = self.detector._detect_node_changes()
        msg = (
            f'Detected {len(node_changes.new_or_modified)} new/modified nodes '
            'and {len(node_changes.deleted)} deleted nodes.'
        )
        logger.report(msg)

        logger.report('Detecting group changes...')
        group_changes = self.detector._detect_group_changes(
            previous_mapping=self.dump_tracker.previous_mapping, current_mapping=self.current_mapping
        )
        msg = (
            f'Detected {len(group_changes.new)} new, {len(group_changes.modified)} modified, '
            f'and {len(group_changes.deleted)} deleted groups.'
        )
        logger.report(msg)

        all_changes = DumpChanges(nodes=node_changes, groups=group_changes)

        if all_changes.is_empty():
            logger.report('No changes detected since last dump and not dumping ungrouped nodes. Nothing to do.')
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
                previous_mapping=self.dump_tracker.previous_mapping,
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
