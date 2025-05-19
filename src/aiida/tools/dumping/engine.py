from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.config import DumpConfig, DumpMode
from aiida.tools.dumping.detect import DumpChangeDetector
from aiida.tools.dumping.logger import DumpLogger
from aiida.tools.dumping.managers.deletion import DeletionManager
from aiida.tools.dumping.managers.group import GroupDumpManager
from aiida.tools.dumping.managers.process import ProcessDumpManager
from aiida.tools.dumping.managers.profile import ProfileDumpManager
from aiida.tools.dumping.utils.helpers import DumpChanges, DumpTimes
from aiida.tools.dumping.utils.paths import DumpPathPolicy

if TYPE_CHECKING:
    from aiida.tools.dumping.mapping import GroupNodeMapping


logger = AIIDA_LOGGER.getChild('tools.dumping.engine')


class DumpEngine:
    """Core engine that orchestrates the dump process."""

    def __init__(
        self,
        base_output_path: Path,
        config: DumpConfig | None = None,
        dump_target_entity: Optional[orm.Node | orm.Group] = None,
    ):
        """Engine constructor that initializes all entities needed for dumping.

        :param path_policy: _description_
        :param config: _description_, defaults to None
        """

        self.config: DumpConfig = config

        self.path_policy = DumpPathPolicy(
            base_output_path=base_output_path,
            config=self.config,
            dump_target_entity=dump_target_entity,
        )

        self.path_policy.prepare_directory(path_to_prepare=base_output_path)

        # --- Initialize Times, Logger, and NodeGroupMapping ---
        self.dump_times, self.dump_logger, self.stored_mapping = self._initialize_times_logger_and_mapping()

        # --- Initialize detector for changes ---
        self.detector = DumpChangeDetector(
            dump_logger=self.dump_logger, path_policy=self.path_policy, config=self.config, dump_times=self.dump_times
        )

        # --- Initialize Managers (pass dependencies) ---
        self.process_manager = ProcessDumpManager(
            config=self.config,
            path_policy=self.path_policy,
            dump_logger=self.dump_logger,
            dump_times=self.dump_times,
        )

    def _initialize_times_logger_and_mapping(
        self,
    ) -> tuple[DumpTimes, DumpLogger, GroupNodeMapping | None]:
        """Initialize dump times, load logger data, and load stored mapping.

        :return: _description_
        """
        logger.debug('Initializing dump times and logger...')

        # Clear log file if overwriting
        if self.config.dump_mode == DumpMode.OVERWRITE and self.path_policy.log_file_path.exists():
            try:
                logger.info(f'Overwrite mode: Deleting existing log file {self.path_policy.log_file_path}')
                self.path_policy.log_file_path.unlink()
            except OSError as e:
                logger.error(f'Failed to delete existing log file: {e}')
                # Decide whether to proceed or raise an error

        # Load log data, stored mapping, and last dump time string from file
        stores_coll, stored_mapping, last_dump_time_str = DumpLogger.load(self.path_policy)

        # Initialize DumpTimes based on loaded time string
        dump_times = DumpTimes.from_last_log_time(last_dump_time_str)
        logger.debug(f'Dump times initialized: Current={dump_times.current}, Last={dump_times.last}')

        # Initialize DumpLogger instance with loaded data
        dump_logger = DumpLogger(
            path_policy=self.path_policy,
            stores=stores_coll,
            last_dump_time_str=last_dump_time_str,
        )
        msg = (
            f'Dump logger initialized. Found {len(dump_logger.calculations)} calc logs, '
            f'{len(dump_logger.workflows)} wf logs, {len(dump_logger.groups)} group logs.'
        )
        logger.debug(msg)

        if stored_mapping:
            msg = f'Loaded stored group mapping with {len(stored_mapping.group_to_nodes)} groups.'
            logger.debug(msg)
        else:
            msg = 'No stored group mapping found in log file.'
            logger.debug(msg)

        return dump_times, dump_logger, stored_mapping

    def _load_config_from_yaml(self) -> DumpConfig | None:
        """Attempts to load DumpConfig from the YAML file in the dump path.

        :return: _description_
        """
        config_path = self.path_policy.config_file_path

        if not config_path.exists():
            logger.debug(f'Config file {config_path} not found. Using default/provided config.')
            return None

        assert self.path_policy.top_level is not None
        config_path_rel = config_path.relative_to(self.path_policy.top_level)
        logger.info(f'Loading configuration from {config_path_rel}...')
        try:
            loaded_config = DumpConfig.parse_yaml_file(path=config_path)
            logger.info('Successfully loaded configuration from file.')
            return loaded_config
        except Exception as e:
            logger.error(f'Failed to load or parse config file {config_path}: {e}', exc_info=True)
            return None

    def _save_config(self) -> None:
        """Save the Pydantic config object to the dump's YAML file."""
        # Use the save method defined on the Pydantic DumpConfig model
        try:
            # This calls self.config.model_dump(mode='json') internally via the serializer
            # and writes to the correct path using yaml.dump
            self.config._save_yaml_file(self.path_policy.config_file_path)
            # The logger message "Dump configuration saved to ..." is now inside save_yaml_file
        except Exception as e:
            # Log error but avoid raising another error during finalization if possible
            # Match original behavior of logging without re-raising here.
            logger.error(f'Failed to save dump configuration during engine finalization: {e}', exc_info=True)

    def dump(self, entity: Optional[orm.ProcessNode | orm.Group] = None) -> None:
        """
        Selects and executes the appropriate dump strategy based on the entity.
        The base output directory is assumed to be prepared by DumpPathPolicy.__init__().
        """
        entity_description = 'profile'
        if isinstance(entity, orm.Group):
            entity_description = f"group '{entity.label}' (PK: {entity.pk})"
        elif isinstance(entity, orm.ProcessNode):
            entity_description = f'process node (PK: {entity.pk})'
        logger.report(f'Starting dump of {entity_description} in mode: {self.config.dump_mode.name}')

        current_mapping: Optional[GroupNodeMapping] = None

        if isinstance(entity, orm.ProcessNode):
            logger.info(f'Executing ProcessNode dump for PK={entity.pk}')
            # For a single ProcessNode, its dump root is the base_output_path.
            # ProcessManager uses DumpPathPolicy to place content within this root.
            self.process_manager.dump(process_node=entity, target_path=self.path_policy.base_output_path)
            try:
                self.process_manager.readme_generator._generate(entity, self.path_policy.base_output_path)
            except Exception as e:
                logger.warning(f'Failed to generate README for process {entity.pk}: {e}')
            current_mapping = None  # No group mapping relevant for single process dump for the main log

        elif isinstance(entity, orm.Group):
            logger.info(f"Executing Group dump for '{entity.label}' (PK: {entity.pk})")
            node_changes, current_mapping = self.detector._detect_all_changes(group=entity)
            group_changes = self.detector._detect_group_changes(
                stored_mapping=self.stored_mapping, current_mapping=current_mapping, specific_group_uuid=entity.uuid
            )
            all_changes = DumpChanges(nodes=node_changes, groups=group_changes)

            if self.config.delete_missing:
                deletion_manager = DeletionManager(
                    config=self.config,
                    path_policy=self.path_policy,
                    dump_logger=self.dump_logger,
                    dump_changes=all_changes,
                    stored_mapping=self.stored_mapping,
                )
                deletion_manager._handle_deleted_entities()

            if self.config.dump_mode == DumpMode.DRY_RUN:
                print(all_changes.to_table())  # Or use logger.report
                return

            # GroupDumpManager needs the specific group and the scoped changes.
            # The DumpPathPolicy instance within GroupDumpManager will be the same as DumpEngine's.
            group_manager = GroupDumpManager(
                group_to_dump=entity,
                config=self.config,
                path_policy=self.path_policy,
                dump_logger=self.dump_logger,
                process_manager=self.process_manager,
                current_mapping=current_mapping,
            )
            # The dump method of GroupDumpManager needs the root path for *this group's content*
            # This root path is determined by DumpPathPolicy.
            group_manager.dump(changes=all_changes)

        else:  # Profile Dump (entity is None)
            logger.info('Executing Profile dump.')
            node_changes, current_mapping = self.detector._detect_all_changes()
            group_changes = self.detector._detect_group_changes(
                stored_mapping=self.stored_mapping, current_mapping=current_mapping
            )
            all_changes = DumpChanges(nodes=node_changes, groups=group_changes)

            if all_changes.is_empty() and not self.config.also_ungrouped:  # Not sure I need the also_ungrouped check
                logger.report('No changes detected since last dump and not dumping ungrouped. Nothing to do.')
            else:
                if self.config.delete_missing:
                    deletion_manager = DeletionManager(
                        config=self.config,
                        path_policy=self.path_policy,
                        dump_logger=self.dump_logger,
                        dump_changes=all_changes,
                        stored_mapping=self.stored_mapping,
                    )
                    deletion_manager._handle_deleted_entities()

                if self.config.dump_mode == DumpMode.DRY_RUN:
                    print(all_changes.to_table())  # Or use logger.report
                    return

                profile_manager = ProfileDumpManager(
                    config=self.config,
                    path_policy=self.path_policy,
                    dump_logger=self.dump_logger,
                    process_manager=self.process_manager,
                    detector=self.detector,
                    current_mapping=current_mapping,
                )
                profile_manager.dump(changes=all_changes)

        logger.report('Saving final dump log and configuration...')
        self.dump_logger.save(current_dump_time=self.dump_times.current, group_node_mapping=current_mapping)
        self._save_config()
        logger.report(f'Dump of {entity_description} completed.')
