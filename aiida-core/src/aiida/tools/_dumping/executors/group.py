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
from aiida.common import AIIDA_LOGGER
from aiida.tools._dumping.executors.collection import CollectionDumpExecutor
from aiida.tools._dumping.tracking import DumpTracker
from aiida.tools._dumping.utils import DumpChanges, DumpPaths

logger = AIIDA_LOGGER.getChild('tools._dumping.executors.group')

if TYPE_CHECKING:
    from aiida.tools._dumping.config import GroupDumpConfig
    from aiida.tools._dumping.executors import ProcessDumpExecutor
    from aiida.tools._dumping.mapping import GroupNodeMapping
    from aiida.tools._dumping.tracking import DumpTracker


class GroupDumpExecutor(CollectionDumpExecutor):
    def __init__(
        self,
        config: GroupDumpConfig,
        dump_paths: DumpPaths,
        dump_tracker: DumpTracker,
        process_dump_executor: ProcessDumpExecutor,
        current_mapping: GroupNodeMapping,
        group: orm.Group,
    ) -> None:
        super().__init__(
            config=config,
            dump_paths=dump_paths,
            dump_tracker=dump_tracker,
            process_dump_executor=process_dump_executor,
            current_mapping=current_mapping,
        )
        self.group: orm.Group = group

        # Explicit type hints
        self.dump_paths: DumpPaths
        self.config: GroupDumpConfig
        self.dump_tracker: DumpTracker
        self.process_dump_executor: ProcessDumpExecutor
        self.current_mapping: GroupNodeMapping

    def dump(self, changes: DumpChanges) -> None:
        """
        Dumps the content of the specific group (self.group).
        The path for this group's content is determined using self.dump_paths.

        :param changes: Scoped DumpChanges relevant to this group, as determined by DumpEngine.
        """
        # The DumpPaths instance knows the overall base_output_path and the dump_target_entity (self.group).
        # It can therefore correctly determine if self.group should be directly in
        # base_output_path or nested under a "groups/" subdirectory.
        current_group_content_root = self.dump_paths.get_path_for_group(group=self.group)

        # Prepare the specific directory for this group's content
        self.dump_paths._prepare_directory(current_group_content_root, is_leaf_node_dir=False)

        # Process lifecycle changes for this group based on group-scoped DumpChanges
        if changes.groups.modified or changes.groups.renamed or changes.groups.node_membership:
            self._handle_group_changes(changes.groups)

        # Process nodes within this group.
        # It needs to use current_group_content_root as the base for placing nodes.
        self._process_group(
            group=self.group,
            changes=changes,
            group_content_path=current_group_content_root,
        )
