###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

"""Base class for collection mirror."""

from __future__ import annotations

import json
from datetime import datetime

from aiida import orm
from aiida.tools.mirror.collector import MirrorNodeCollector, MirrorNodeContainer
from aiida.tools.mirror.config import (
    MirrorMode,
    NodeCollectorConfig,
)
from aiida.tools.mirror.logger import MirrorLogger
from aiida.tools.mirror.utils import (
    MirrorPaths,
    prepare_mirror_path,
)


class CollectionBaseMirror:
    def __init__(
        self,
        mirror_mode: MirrorMode | None = None,
        mirror_paths: MirrorPaths | None = None,
        last_mirror_time: datetime | None = None,
        mirror_logger: MirrorLogger | None = None,
        node_collector_config: NodeCollectorConfig | None = None,
    ):
        self.mirror_mode = mirror_mode or MirrorMode.INCREMENTAL
        self.mirror_paths = mirror_paths or MirrorPaths()
        self.last_mirror_time = last_mirror_time
        self.mirror_logger = mirror_logger
        self.node_collector_config = node_collector_config or NodeCollectorConfig()

        if not mirror_logger:
            if self.mirror_mode.OVERWRITE:
                self.mirror_logger = mirror_logger = MirrorLogger(mirror_paths=self.mirror_paths)
            else:
                self.mirror_logger = self.load_mirror_logger()

    def load_mirror_logger(self):
        try:
            mirror_logger = MirrorLogger.from_file(mirror_paths=self.mirror_paths)
        except (json.JSONDecodeError, OSError):
            mirror_logger = MirrorLogger(mirror_paths=self.mirror_paths)

        return mirror_logger

    def _pre_mirror(self, top_level_caller: bool = False) -> None:
        """_summary_"""
        _ = prepare_mirror_path(
            path_to_validate=self.mirror_paths.absolute,
            mirror_mode=self.mirror_mode,
            safeguard_file=self.mirror_paths.safeguard_path,
            top_level_caller=top_level_caller,
        )

        safeguard_file_path = self.mirror_paths.safeguard_path

        try:
            with safeguard_file_path.open('r') as fhandle:
                last_mirror_time = datetime.fromisoformat(fhandle.readlines()[-1].strip().split()[-1]).astimezone()
        except (IndexError, FileNotFoundError):
            last_mirror_time = None

        self.safeguard_file_path = safeguard_file_path
        self.last_mirror_time = last_mirror_time
        self.current_mirror_time = datetime.now().astimezone()

    def _post_mirror(self) -> None:
        """_summary_"""
        self.mirror_logger.save_log()

        # Append the current mirror time to safeguard file
        with self.safeguard_file_path.open('a') as fhandle:
            fhandle.write(f'Last mirror time: {self.current_mirror_time.isoformat()}\n')

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
