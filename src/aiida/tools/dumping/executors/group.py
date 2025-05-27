###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Executor that orchestrates dumping an AiiDA group."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.executors.collection import CollectionDumpExecutor
from aiida.tools.dumping.tracking import DumpTracker
from aiida.tools.dumping.utils import DumpChanges, DumpPaths

logger = AIIDA_LOGGER.getChild('tools.dumping.executors.profile')

if TYPE_CHECKING:
    from aiida.tools.dumping.config import DumpConfig
    from aiida.tools.dumping.executors.collection import CollectionDumpExecutor
    from aiida.tools.dumping.executors.process import ProcessDumpExecutor
    from aiida.tools.dumping.mapping import GroupNodeMapping
    from aiida.tools.dumping.tracking import DumpTracker


class GroupDumpExecutor(CollectionDumpExecutor):
    def __init__(
        self,
        config: DumpConfig,
        dump_paths: DumpPaths,
        dump_tracker: DumpTracker,
        process_dump_executor: ProcessDumpExecutor,
        group_to_dump: orm.Group,
        current_mapping: GroupNodeMapping,
    ) -> None:
        super().__init__(
            config=config,
            dump_paths=dump_paths,
            dump_tracker=dump_tracker,
            process_dump_executor=process_dump_executor,
            current_mapping=current_mapping,
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
        current_group_content_root = self.dump_paths.get_path_for_group(
            group=self.group_to_dump,
            parent_group_content_path=None,  # This is the top-level group for this manager's operation
        )

        # 1. Prepare the specific directory for this group's content.
        self.dump_paths.prepare_directory(current_group_content_root, is_leaf_node_dir=False)

        # Register this group in the logger with its actual content path. -> NOTE: This should be called in
        # `_handle_group_changes`
        # self._register_group_and_prepare_path(group=self.group_to_dump, group_content_path=current_group_content_root)

        # 2. Process lifecycle changes FOR THIS GROUP.
        #    The `changes.groups` object should have been pre-filtered by DumpEngine
        #    to only contain changes relevant to `self.group_to_dump`.
        #    If _handle_group_changes in CollectionDumpExecutor is designed to work on
        #    scoped GroupChanges for a single group, this is fine.
        if changes.groups.modified or changes.groups.renamed or changes.groups.node_membership:
            self._handle_group_changes(changes.groups)

        # 3. Process nodes within this group.
        # _process_group is inherited from CollectionDumpExecutor.
        # It needs to use current_group_content_root as the base for placing nodes.
        self._process_group(
            group=self.group_to_dump,
            changes=changes,  # Scoped changes
            group_content_root_path=current_group_content_root,  # Explicitly pass the root
        )

        # 4. Update stats for this specific group.
        self._update_directory_stats(
            entity_uuid=self.group_to_dump.uuid, path=current_group_content_root, registry_key='groups'
        )
