###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from pathlib import Path

from aiida.tools.dumping.config import BaseDumpConfig
from aiida.tools.dumping.logger import DumpLogger


class BaseDumper:
    """Base class for all Dumper classes with shared attributes."""

    def __init__(
        self,
        base_dump_config: BaseDumpConfig | None = None,
        dump_logger: DumpLogger | None = None,
    ):
        self.base_dump_config = base_dump_config or BaseDumpConfig()

        # Unpack values for direct access
        self.dump_parent_path = self.base_dump_config.dump_parent_path or Path.cwd()
        self.overwrite = self.base_dump_config.overwrite
        self.incremental = self.base_dump_config.incremental
        self.last_dump_time = self.base_dump_config.last_dump_time

        # Keep logger
        self.dump_logger = dump_logger or DumpLogger(dump_parent_path=self.dump_parent_path)
