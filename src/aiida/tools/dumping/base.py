###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from pathlib import Path
from datetime import datetime


class BaseDumper:
    def __init__(
        self,
        dump_parent_path: Path = Path.cwd(),
        overwrite: bool = False,
        incremental: bool = True,
        last_dump_time: datetime | None = None,
    ):
        self.dump_parent_path = dump_parent_path
        self.overwrite = overwrite
        self.incremental = incremental
        self.last_dump_time = last_dump_time