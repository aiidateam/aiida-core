from __future__ import annotations

from typing import TYPE_CHECKING

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.config import DumpConfig, DumpMode, ProfileDumpSelection
from aiida.tools.dumping.detect import DumpChangeDetector
from aiida.tools.dumping.logger import DumpLogger
from aiida.tools.dumping.managers.deletion import DeletionManager
from aiida.tools.dumping.managers.process import ProcessDumpManager
from aiida.tools.dumping.utils.helpers import DumpChanges, DumpTimes, GroupChanges
from aiida.tools.dumping.utils.paths import DumpPaths

if TYPE_CHECKING:
    from aiida.tools.dumping.mapping import GroupNodeMapping


logger = AIIDA_LOGGER.getChild('tools.dumping.engine')


class DumpEngine:
    """Core engine that orchestrates the dump process."""

    def __init__(self, dump_paths: DumpPaths, config: DumpConfig | None = None):
        """Engine constructor that initializes all entities needed for dumping.

        :param dump_paths: _description_
        :param config: _description_, defaults to None
        """

        self.dump_paths = dump_paths

        # --- Resolve Configuration from file and possibly passed values ---
        # Loads from YAML if present and merges with the passed config object
        # if not isinstance(config, DumpConfig):
        #     msg = f"DumpEngine expects a DumpConfig object, got {type(config)}"
        #     raise TypeError(msg)
        self.config: DumpConfig = config

        # --- Initialize Times, Logger, and NodeGroupMapping ---
        self.dump_times, self.dump_logger, self.stored_mapping = self._initialize_times_logger_and_mapping()

        # --- Initialize detector for changes ---
        self.detector = DumpChangeDetector(self.dump_logger, self.config, self.dump_times)

        # --- Initialize Managers (pass dependencies) ---
        self.process_manager = ProcessDumpManager(
            config=self.config,
            dump_paths=dump_paths,
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
        if self.config.dump_mode == DumpMode.OVERWRITE and self.dump_paths.log_path.exists():
            try:
                logger.info(f'Overwrite mode: Deleting existing log file {self.dump_paths.log_path}')
                self.dump_paths.log_path.unlink()
            except OSError as e:
                logger.error(f'Failed to delete existing log file: {e}')
                # Decide whether to proceed or raise an error

        # Load log data, stored mapping, and last dump time string from file
        stores_coll, stored_mapping, last_dump_time_str = DumpLogger.load(self.dump_paths)

        # Initialize DumpTimes based on loaded time string
        dump_times = DumpTimes.from_last_log_time(last_dump_time_str)
        logger.debug(f'Dump times initialized: Current={dump_times.current}, Last={dump_times.last}')

        # Initialize DumpLogger instance with loaded data
        dump_logger = DumpLogger(
            dump_paths=self.dump_paths,
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
        config_path = self.dump_paths.config_path

        if not config_path.exists():
            logger.debug(f'Config file {config_path} not found. Using default/provided config.')
            return None

        assert self.dump_paths.top_level is not None
        config_path_rel = config_path.relative_to(self.dump_paths.top_level)
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
            self.config._save_yaml_file(self.dump_paths.config_path)
            # The logger message "Dump configuration saved to ..." is now inside save_yaml_file
        except Exception as e:
            # Log error but avoid raising another error during finalization if possible
            # Match original behavior of logging without re-raising here.
            logger.error(f'Failed to save dump configuration during engine finalization: {e}', exc_info=True)

    def dump(self, entity: orm.ProcessNode | orm.Group | None = None) -> None:
        """Selects and executes the appropriate dump strategy.

        :param entity: _description_, defaults to None
        """

        entity_type_msg = 'Starting dump process of '
        if entity is None:
            entity_type_msg += 'default profile'
        elif isinstance(entity, orm.Group):
            entity_type_msg += f'group `{entity.label}`'
        elif isinstance(entity, orm.ProcessNode):
            entity_type_msg += f'process with pk `{entity.pk}`'

        entity_type_msg += f' in mode: {self.config.dump_mode.name}'

        logger.report(entity_type_msg)

        # --- Prepare Top-Level Path ---
        if not self.config.dump_mode == DumpMode.DRY_RUN:
            try:
                DumpPaths._prepare_dump_path(
                    path_to_validate=self.dump_paths.absolute,
                    dump_mode=self.config.dump_mode,
                    safeguard_file=self.dump_paths.safeguard_file,
                )
            except (FileNotFoundError, FileExistsError, ValueError, OSError) as e:
                logger.critical(f'Failed to prepare dump directory {self.dump_paths.child}: {e}')
                raise e

        # --- For process dump, I don't need any complicated logic
        if isinstance(entity, orm.ProcessNode):
            logger.info(f'Executing Process dump for node: PK={entity.pk}')
            process_node = entity
            process_top_level_path = self.dump_paths.absolute
            logger.info(f'Dispatching node {process_node.pk} to ProcessManager...')
            self.process_manager.dump(
                process_node=process_node,
                target_path=process_top_level_path,
            )
            logger.info(f'ProcessManager finished processing node: PK={process_node.pk}')
            try:
                self.process_manager.readme_generator._generate(process_node, process_top_level_path)
            except Exception as e:
                logger.warning(f'Failed to generate README for process {process_node.pk}: {e}')
            logger.info(f'Finished Process dump for node: PK={entity.pk}')

            # No mapping evaluated for ProcessNode
            self.dump_logger.save(self.dump_times.current)

        else:
            from aiida.tools.dumping.managers.profile import ProfileDumpManager

            # TODO: This is a bit of a hack right now such that there
            # TODO: is no additional unneccessary nesting for group dump
            # TODO: We use the same code as for the dumping of a profile, but with only one group selected
            if isinstance(entity, orm.Group):
                self.config.organize_by_groups = False
                self.config.profile_dump_selection = ProfileDumpSelection.SPECIFIC
                self.config.groups = [entity.uuid]

            # --- Change Detection (for Dumping) ---
            logger.info('Detecting node changes for dump...')
            # node_changes now holds a NodeChanges object, current_mapping holds the mapping
            node_changes, current_mapping = self.detector._detect_all_changes(
                group=entity if isinstance(entity, orm.Group) else None
            )
            # TODO: See if I should pass the mapping here or create it in the Manager
            self.current_mapping = current_mapping

            logger.info('Detecting group changes for dump...')
            group_changes: GroupChanges
            group_changes = self.detector._detect_group_changes(
                stored_mapping=self.stored_mapping,  # Use mapping loaded at init
                current_mapping=current_mapping,  # Use mapping from node detection
                specific_group_uuid=(entity.uuid if isinstance(entity, orm.Group) else None),
            )

            # Combine detected changes
            all_changes = DumpChanges(
                nodes=node_changes,
                groups=group_changes,
            )

            # --- Check if any changes were detected ---
            no_node_changes = len(all_changes.nodes.new_or_modified) == 0 and len(all_changes.nodes.deleted) == 0
            no_group_changes = (
                len(all_changes.groups.new) == 0
                and len(all_changes.groups.deleted) == 0
                and len(all_changes.groups.modified) == 0
                and len(all_changes.groups.renamed) == 0
                and len(all_changes.groups.node_membership) == 0
            )

            # If `als_ungrouped`
            if (no_node_changes and no_group_changes) and not self.config.also_ungrouped:
                logger.report('No changes detected since last dump. Nothing to do.')
                self.dump_logger.save(self.dump_times.current, self.current_mapping)
                self._save_config()
                return

            # --- Handle Deletion First (if requested) ---
            if self.config.delete_missing:
                logger.info('Deletion requested. Handling deleted entities...')
                # --- Change Detection (needed *only* for deletion info) ---
                logger.info('Detecting changes to identify deletions...')
                # Detect node changes (yields NodeChanges and mapping)
                # TODO: Independent of groups. Or is it?
                deletion_manager = DeletionManager(
                    config=self.config,
                    dump_paths=self.dump_paths,
                    dump_logger=self.dump_logger,
                    dump_changes=all_changes,
                    stored_mapping=self.stored_mapping,
                )
                deletion_manager._handle_deleted_entities()

            if self.config.dump_mode == DumpMode.DRY_RUN:
                change_table = all_changes.to_table()
                print(change_table)
                return

            profile_manager = ProfileDumpManager(
                selected_group=entity,
                config=self.config,
                dump_paths=self.dump_paths,
                dump_logger=self.dump_logger,
                process_manager=self.process_manager,
                current_mapping=current_mapping,
                detector=self.detector,
            )

            # Call the newly instantiated ProfileDumpManager
            profile_manager.dump(changes=all_changes)

            # No mapping evaluated for ProcessNode
            self.dump_logger.save(self.dump_times.current, current_mapping)

        # --- Finalize ---
        logger.report('Saving final dump log, mapping, and configuration...')
        self._save_config()
