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


class BaseMirror:
    def __init__(
        self,
        mirror_mode: MirrorMode | None = None,
        mirror_paths: MirrorPaths | None = None,
        last_mirror_time: datetime | None = None,
        mirror_logger: MirrorLogger | None = None,
    ):
        self.mirror_mode = mirror_mode or MirrorMode.INCREMENTAL
        self.mirror_paths = mirror_paths or MirrorPaths()
        self.last_mirror_time = last_mirror_time
        self.mirror_logger = self.set_mirror_logger(mirror_logger=mirror_logger)


    def set_mirror_logger(self, mirror_logger: MirrorLogger | None = None):
        """If in OVERWRITE mode or if loading from file fails, create a new instance

        :param mirror_logger: Optional existing logger instance to use
        :return: The appropriate MirrorLogger instance
        """
        
        # If in OVERWRITE mode, create a new instance
        if self.mirror_mode.OVERWRITE:
            return MirrorLogger(mirror_paths=self.mirror_paths)

        # Use provided mirror_logger if one is passed in
        if mirror_logger is not None:
            return mirror_logger
        
        # Try to load from file, fall back to new instance on failure
        try:
            return MirrorLogger.from_file(mirror_paths=self.mirror_paths)
        except (json.JSONDecodeError, OSError):
            return MirrorLogger(mirror_paths=self.mirror_paths)

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