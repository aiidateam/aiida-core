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
from aiida.tools.dumping.logger import DumpLogger
from aiida.tools.dumping.managers.collection import CollectionDumpManager
from aiida.tools.dumping.utils.helpers import DumpChanges
from aiida.tools.dumping.utils.paths import DumpPathPolicy

logger = AIIDA_LOGGER.getChild('tools.dumping.strategies.profile')

if TYPE_CHECKING:
    from aiida.tools.dumping.config import DumpConfig
    from aiida.tools.dumping.logger import DumpLogger
    from aiida.tools.dumping.managers.collection import CollectionDumpManager
    from aiida.tools.dumping.managers.process import ProcessDumpManager
    from aiida.tools.dumping.mapping import GroupNodeMapping


class GroupDumpManager(CollectionDumpManager):
    def __init__(
        self,
        config: DumpConfig,
        path_policy: DumpPathPolicy,
        dump_logger: DumpLogger,
        process_manager: ProcessDumpManager,
        current_mapping: GroupNodeMapping,
        group_to_dump: orm.Group,
    ) -> None:
        super().__init__(
            config=config,
            path_policy=path_policy,
            process_manager=process_manager,
            current_mapping=current_mapping,
            dump_logger=dump_logger,
        )
        self.group_to_dump = group_to_dump

    def dump(self, changes: DumpChanges) -> None:
        """
        Dumps the content of the specific group (self.group_to_dump).
        The path for this group's content is determined using self.path_policy.

        :param changes: Scoped DumpChanges relevant to this group, as determined by DumpEngine.
        """
        # --- Determine the root path for THIS group's content ---
        # The PathPolicy instance (self.path_policy) was initialized by DumpEngine.
        # It knows the overall base_output_path and the dump_target_entity (which is self.group_to_dump).
        # It can therefore correctly determine if self.group_to_dump should be directly in
        # base_output_path or nested under a "groups/" subdirectory.
        current_group_content_root = self.path_policy.get_path_for_group_content(
            group=self.group_to_dump,
            parent_group_content_path=None,  # This is the top-level group for this manager's operation
        )

        logger.info(
            f"Executing GroupDumpManager for group '{self.group_to_dump.label}' "
            f"into determined path '{current_group_content_root}'"
        )

        # 1. Prepare the specific directory for this group's content.
        self.path_policy.prepare_directory(current_group_content_root, is_leaf_node_dir=False)

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

        # # 5. Recursive dump of child groups (if applicable)
        # if self.config.recursive_groups:
        #     logger.info(f"Checking for child groups of '{self.group_to_dump.label}' for recursive dump.")
        #     # This part requires careful implementation:
        #     #   - How to get child groups (e.g., from DB, or from `current_mapping` if comprehensive).
        #     #   - How to get scoped `DumpChanges` for each child.
        #     #   - The `DumpEngine` is likely better suited to manage the recursive calls to
        #     #     `GroupDumpManager` instances, providing each with its correct context and changes.
        #     #   - If GroupDumpManager handles recursion itself, it becomes much more complex.

        #     # Conceptual placeholder for how child group dumping would be initiated:
        #     # child_groups = self.detector.get_child_groups(self.group_to_dump, self.current_mapping)
        #     # for child_group in child_groups:
        #     #     logger.info(f"Recursively processing child group '{child_group.label}'.")
        #     #     # Path for the child group's content, nested under the current group's content root
        #     #     child_content_root = self.path_policy.get_path_for_group_content(
        #     #         group=child_group,
        #     #         parent_group_content_path=current_group_content_root # Key for nesting
        #     #     )
        #     #     # Get scoped changes for the child group
        #     #     child_node_changes, child_current_mapping = self.detector._detect_all_changes(group=child_group)
        #     #     child_group_changes = self.detector._detect_group_changes(
        #     #                                 stored_mapping=self.stored_mapping, # Or a relevant subset
        #     #                                 current_mapping=child_current_mapping,
        #     #                                 specific_group_uuid=child_group.uuid)
        #     #     scoped_child_changes = DumpChanges(nodes=child_node_changes, groups=child_group_changes)

        #     #     # Either recursively call self.dump (if re-entrant and state is managed)
        #     #     # OR, more cleanly, the DumpEngine would manage this loop and create
        #     #     # new GroupDumpManager instances for children.
        #     #     # For now, let's assume DumpEngine would handle the iteration and calls.
        #     #     # If this manager calls itself, it needs to be careful about state.
        #     pass  # End conceptual recursion block

        logger.info(f"Finished GroupDumpManager for group '{self.group_to_dump.label}'.")

    def _update_single_group_stats(self, group: orm.Group, group_content_path: Path) -> None:
        # ... (implementation as before) ...
        logger.info(f"Calculating final directory stats for group '{group.label}'.")
        group_log_entry = self.dump_logger.groups.get_entry(group.uuid)

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
            dir_mtime, dir_size = DumpPathPolicy.get_directory_stats(group_content_path)
            group_log_entry.dir_mtime = dir_mtime
            group_log_entry.dir_size = dir_size
            logger.debug(f'Updated stats for group {group.uuid}: mtime={dir_mtime}, size={dir_size}')
        except Exception as e:
            logger.error(f'Failed to calculate/update stats for group {group.uuid} at {group_content_path}: {e}')
