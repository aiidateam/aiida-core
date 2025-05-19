
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

from typing import TYPE_CHECKING

from aiida import orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.config import ProfileDumpSelection
from aiida.tools.dumping.detect import DumpChangeDetector
from aiida.tools.dumping.logger import DumpLogger
from aiida.tools.dumping.managers.collection import CollectionDumpManager
from aiida.tools.dumping.utils.helpers import DumpChanges
from aiida.tools.dumping.utils.paths import DumpPaths

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
        dump_paths: DumpPaths,
        dump_logger: DumpLogger,
        detector: DumpChangeDetector,
        process_manager: ProcessDumpManager,
        current_mapping: GroupNodeMapping,
        group_to_dump: orm.Group,
    ) -> None:
        super().__init__(
            config=config,
            dump_paths=dump_paths,
            process_manager=process_manager,
            detector=detector,
            current_mapping=current_mapping,
            dump_logger=dump_logger
        )
        self.group_to_dump = group_to_dump

    def dump(self, changes: DumpChanges) -> None:
        """Dumps the group content by orchestrating helper methods."""
        logger.info('Executing GroupDumpManager')

        # 1. Handle Group Lifecycle (using Group Manager)
        #    This applies changes detected earlier (new/deleted groups, membership)
        #    Directory creation/deletion for groups happens here or in DeletionManager
        logger.info('Processing group lifecycle and membership changes...')
        self._handle_group_changes(changes.groups)

        # 2. Determine which groups need node processing based on config
        #    (e.g., all groups, specific groups)
        # groups_to_process = self._determine_groups_to_process()

        # 3. Process nodes within each selected group
        logger.info('Processing nodes within groups...')
        # for group in groups_to_process:
            # _process_group handles finding nodes for this group,
            # adding descendants if needed, and calling node_manager.dump_nodes
        import ipdb; ipdb.set_trace()
        self._process_group(self.group_to_dump, changes)

        # 5. Update final stats for logged groups after all dumping is done
        # self._update_group_stats()

        logger.info('Finished ProfileDumpManager.')
