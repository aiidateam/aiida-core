###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

"""Base class for collection mirror."""

# TODO: Fix `last_mirror_time`

from __future__ import annotations

import json
from datetime import datetime

from aiida import orm
from aiida.tools.mirror.collector import MirrorNodeCollector, MirrorNodeContainer
from aiida.tools.mirror.config import (
    MirrorMode,
    NodeCollectorConfig,
)
from aiida.tools.mirror.base import BaseMirror
from aiida.tools.mirror.logger import MirrorLogger
from aiida.tools.mirror.utils import (
    MirrorPaths,
    prepare_mirror_path,
)


class BaseCollectionMirror(BaseMirror):
    def __init__(
        self,
        mirror_mode: MirrorMode | None = None,
        mirror_paths: MirrorPaths | None = None,
        last_mirror_time: datetime | None = None,
        mirror_logger: MirrorLogger | None = None,
        node_collector_config: NodeCollectorConfig | None = None,
    ):
        super().__init__(
            mirror_mode=mirror_mode,
            mirror_paths=mirror_paths,
            last_mirror_time=last_mirror_time,
            mirror_logger=mirror_logger,
        )

        self.node_collector_config = node_collector_config or NodeCollectorConfig()

    def get_node_container(self, group: orm.Group | None = None) -> MirrorNodeContainer:
        """
        Returns a NodeContainer by collecting nodes using the NodeDumpCollector.

        Returns:
            NodeContainer: The collected node container
        """
        node_collector = MirrorNodeCollector(
            config=self.node_collector_config,
            last_mirror_time=self.last_mirror_time,
            mirror_logger=self.mirror_logger,
        )

        return node_collector.collect(group=group)
