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
from typing import Optional, Union

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
        base_output_path: Path,
        config: DumpConfig | None = None,
        dump_target_entity: Optional[Union[orm.Node, orm.Group, Profile]] = None,
    ):
        """Engine constructor that initializes all entities needed for dumping.

        :param dump_paths: _description_
        :param config: _description_, defaults to None
        """

        self.config: DumpConfig = config or DumpConfig()

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

        # --- Initialize Managers (pass dependencies) ---
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
        logger.debug('Initializing dump times and logger...')

        # Clear log file if overwriting
        if self.config.dump_mode == DumpMode.OVERWRITE and self.dump_paths.tracking_log_file_path.exists():
            try:
                logger.info(f'Overwrite mode: Deleting existing log file {self.dump_paths.tracking_log_file_path}')
                self.dump_paths.tracking_log_file_path.unlink()
            except OSError as e:
                logger.error(f'Failed to delete existing log file: {e}')
                # Decide whether to proceed or raise an error

        # Load log data, stored mapping, and last dump time string from file
        dump_tracker, stored_mapping = DumpTracker.load(self.dump_paths)
        last_dump_time_str = dump_tracker._last_dump_time_str

        # Initialize DumpTimes based on loaded time string
        dump_times = DumpTimes.from_last_log_time(last_dump_time_str)
        logger.debug(f'Dump times initialized: Current={dump_times.current}, Last={dump_times.last}')

        # Initialize DumpTracker instance with loaded data
        msg: str = (
            f'Dump logger initialized. '
            f'Found {len(dump_tracker.registries["calculations"])} calculation logs, '
            f'{len(dump_tracker.registries["workflows"])} workflow logs, '
            f'{len(dump_tracker.registries["groups"])} group logs.'
        )
        logger.debug(msg)

        if stored_mapping:
            msg = f'Loaded stored group mapping with {len(stored_mapping.group_to_nodes)} groups.'
            logger.debug(msg)
        else:
            msg = 'No stored group mapping found in log file.'
            logger.debug(msg)

        return dump_times, dump_tracker, stored_mapping

    def dump(self, entity: Optional[orm.ProcessNode | orm.Group | Profile] = None) -> None:
        """
        Selects and executes the appropriate dump strategy based on the entity.
        The base output directory is assumed to be prepared by DumpPaths.__init__().
        """
        if isinstance(entity, orm.ProcessNode):
            entity_description = f'process node (PK: {entity.pk})'
        elif isinstance(entity, orm.Group):
            entity_description = f'group `{entity.label}` (PK: {entity.pk})'
        elif isinstance(entity, Profile):
            entity_description = f'profile `{entity.name}`'
        else:
            msg = f'Entity type {type(entity)} not supported.'
            raise ValueError(msg)

        msg = f'Starting dump of {entity_description} in {self.config.dump_mode.name.lower()} mode.'
        if self.config.dump_mode != DumpMode.DRY_RUN:
            logger.report(msg)

        current_mapping = None

        if isinstance(entity, orm.ProcessNode):
            logger.info(f'Executing ProcessNode dump for PK={entity.pk}')
            # For a single ProcessNode, its dump root is the base_output_path.
            # ProcessManager uses DumpPaths to place content within this root.
            self.process_dump_executor.dump(process_node=entity, target_path=self.dump_paths.base_output_path)
            self.process_dump_executor.readme_generator._generate(entity, self.dump_paths.base_output_path)

        elif isinstance(entity, orm.Group):
            logger.info(f"Executing Group dump for '{entity.label}' (PK: {entity.pk})")
            node_changes = self.detector._detect_node_changes(group=entity)
            current_mapping = GroupNodeMapping.build_from_db()
            group_changes = self.detector._detect_group_changes(
                stored_mapping=self.stored_mapping, current_mapping=current_mapping, specific_group_uuid=entity.uuid
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
                print(all_changes.to_table())  # Or use logger.report
                return

            # GroupDumpExecutor needs the specific group and the scoped changes.
            # The DumpPaths instance within GroupDumpExecutor will be the same as DumpEngine's.
            group_dump_executor = GroupDumpExecutor(
                group_to_dump=entity,
                config=self.config,
                dump_paths=self.dump_paths,
                dump_tracker=self.dump_tracker,
                process_dump_executor=self.process_dump_executor,
                current_mapping=current_mapping,
            )
            group_dump_executor.dump(changes=all_changes)

        elif isinstance(entity, Profile):
            if not self.config.all_entries and not self.config.filters_set:
                # NOTE: Hack for now, delete empty directory again. Ideally don't even create in the first place
                # Need to check again where it is actually created...
                self.dump_paths.safe_delete_directory(path=self.dump_paths.base_output_path)
                return

            node_changes = self.detector._detect_node_changes()
            current_mapping = GroupNodeMapping.build_from_db()
            group_changes = self.detector._detect_group_changes(
                stored_mapping=self.stored_mapping, current_mapping=current_mapping
            )
            all_changes = DumpChanges(nodes=node_changes, groups=group_changes)

            if all_changes.is_empty() and not self.config.also_ungrouped:  # Not sure I need the also_ungrouped check
                logger.report('No changes detected since last dump and not dumping ungrouped. Nothing to do.')
            else:
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

                profile_dump_executor = ProfileDumpExecutor(
                    config=self.config,
                    dump_paths=self.dump_paths,
                    dump_tracker=self.dump_tracker,
                    process_dump_executor=self.process_dump_executor,
                    detector=self.detector,
                    current_mapping=current_mapping,
                )
                profile_dump_executor.dump(changes=all_changes)

        logger.report(f'Saving final dump log to file `{DumpPaths.TRACKING_LOG_FILE_NAME}`.')
        self.dump_tracker.save(current_dump_time=self.dump_times.current, group_node_mapping=current_mapping)
