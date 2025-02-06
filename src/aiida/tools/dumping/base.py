###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class BaseDumper:
    dump_parent_path: Path | None = None
    overwrite: bool = False
    incremental: bool = True
    last_dump_time: datetime | None = None

    def __post_init__(self):
        if self.dump_parent_path is None:
            self.dump_parent_path = Path.cwd()
