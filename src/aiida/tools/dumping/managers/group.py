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

from pathlib import Path
from typing import TYPE_CHECKING

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.tracking import DumpTracker
from aiida.tools.dumping.managers.collection import CollectionDumpManager
from aiida.tools.dumping.utils.helpers import DumpChanges
from aiida.tools.dumping.utils.paths import DumpPaths

logger = AIIDA_LOGGER.getChild('tools.dumping.strategies.profile')

if TYPE_CHECKING:
    from aiida.tools.dumping.config import DumpConfig
    from aiida.tools.dumping.tracking import DumpTracker
    from aiida.tools.dumping.managers.collection import CollectionDumpManager
    from aiida.tools.dumping.managers.process import ProcessDumpManager
    from aiida.tools.dumping.mapping import GroupNodeMapping


class GroupDumpManager(CollectionDumpManager):
    def __init__(
        self,
        config: DumpConfig,
        dump_paths: DumpPaths,
        dump_tracker: DumpTracker,
        process_manager: ProcessDumpManager,
        current_mapping: GroupNodeMapping,
        group_to_dump: orm.Group,
    ) -> None:
        super().__init__(
            config=config,
            dump_paths=dump_paths,
            process_manager=process_manager,
            current_mapping=current_mapping,
            dump_tracker=dump_tracker,
        )
        self.group_to_dump = group_to_dump

    def dump(self, changes: DumpChanges) -> None:
        """
        Dumps the content of the specific group (self.group_to_dump).
        The path for this group's content is determined using self.dump_paths.

        :param changes: Scoped DumpChanges relevant to this group, as determined by DumpEngine.
        """
        # --- Determine the root path for THIS group's content ---
        # The PathPolicy instance (self.dump_paths) was initialized by DumpEngine.
        # It knows the overall base_output_path and the dump_target_entity (which is self.group_to_dump).
        # It can therefore correctly determine if self.group_to_dump should be directly in
        # base_output_path or nested under a "groups/" subdirectory.
        current_group_content_root = self.dump_paths.get_path_for_group_content(
            group=self.group_to_dump,
            parent_group_content_path=None,  # This is the top-level group for this manager's operation
        )

        logger.info(
            f"Executing GroupDumpManager for group '{self.group_to_dump.label}' "
            f"into determined path '{current_group_content_root}'"
        )

        # 1. Prepare the specific directory for this group's content.
        self.dump_paths.prepare_directory(current_group_content_root, is_leaf_node_dir=False)

        # Register this group in the logger with its actual content path.
        self._register_group_and_prepare_path(group=self.group_to_dump, group_content_path=current_group_content_root)

        # 2. Process lifecycle changes FOR THIS GROUP.
        #    The `changes.groups` object should have been pre-filtered by DumpEngine
        #    to only contain changes relevant to `self.group_to_dump`.
        #    If _handle_group_changes in CollectionDumpManager is designed to work on
        #    scoped GroupChanges for a single group, this is fine.
        if changes.groups.modified or changes.groups.renamed or changes.groups.node_membership:
            logger.info(f"Processing lifecycle/membership for group '{self.group_to_dump.label}'.")
            self._handle_group_changes(changes.groups)

        # 3. Process nodes within this group.
        logger.info(f"Processing nodes for group '{self.group_to_dump.label}'.")
        # _process_group is inherited from CollectionDumpManager.
        # It needs to use current_group_content_root as the base for placing nodes.
        self._process_group(
            group=self.group_to_dump,
            changes=changes,  # Scoped changes
            group_content_root_path=current_group_content_root,  # Explicitly pass the root
        )

        # 4. Update stats for this specific group.
        self._update_single_group_stats(self.group_to_dump, current_group_content_root)

        logger.info(f"Finished GroupDumpManager for group '{self.group_to_dump.label}'.")

    def _update_single_group_stats(self, group: orm.Group, group_content_path: Path) -> None:
        # ... (implementation as before) ...
        logger.info(f"Calculating final directory stats for group '{group.label}'.")
        group_log_entry = self.dump_tracker.groups.get_entry(group.uuid)

        if not group_log_entry:
            logger.warning(f"Log entry for group '{group.label}' not found. Cannot update stats.")
            return
        if not group_content_path.is_dir():
            logger.warning(
                f'Group content path {group_content_path} for UUID {group.uuid} is not a directory. Skipping stats.'
            )
            return
        logger.debug(f'Calculating stats for group directory: {group_content_path} (UUID: {group.uuid})')
        try:
            dir_mtime, dir_size = DumpPaths.get_directory_stats(group_content_path)
            group_log_entry.dir_mtime = dir_mtime
            group_log_entry.dir_size = dir_size
            logger.debug(f'Updated stats for group {group.uuid}: mtime={dir_mtime}, size={dir_size}')
        except Exception as e:
            logger.error(f'Failed to calculate/update stats for group {group.uuid} at {group_content_path}: {e}')
