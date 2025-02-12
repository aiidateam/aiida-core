###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from datetime import datetime
from pathlib import Path

from aiida.tools.dumping.config import BaseDumpConfig
from aiida.tools.dumping.logger import DumpLogger


class BaseDumper:
    """Base class for all Dumper classes with shared attributes."""

    def __init__(
        self,
        dump_parent_path: Path | None = None,
        overwrite: bool = False,
        incremental: bool = True,
        last_dump_time: datetime | None = None,
        dump_logger: DumpLogger | None = None,
        base_dump_config: BaseDumpConfig | None = None,
    ):
        if base_dump_config:
            self.dump_parent_path = base_dump_config.dump_parent_path
            self.overwrite = base_dump_config.overwrite
            self.incremental = base_dump_config.incremental
            self.last_dump_time = base_dump_config.last_dump_time
            self.dump_logger = dump_logger or DumpLogger(dump_parent_path=self.dump_parent_path)
        else:
            self.dump_parent_path = dump_parent_path or Path.cwd()
            self.overwrite = overwrite
            self.incremental = incremental
            self.last_dump_time = last_dump_time
            self.dump_logger = dump_logger or DumpLogger(dump_parent_path=self.dump_parent_path)
