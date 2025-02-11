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
class BaseDumpConfig:
    """Container for shared arguments of all Dumper classes."""

    dump_parent_path: Path | None = None
    overwrite: bool = False
    incremental: bool = True
    check_dirs: bool = False
    # TODO: Make this a per-class attribute?
    last_dump_time: datetime | None = None

    def __post_init__(self):
        if self.dump_parent_path is None:
            self.dump_parent_path = Path.cwd()


@dataclass
class ProcessDumpConfig:
    """Arguments for dumping process data."""

    include_inputs: bool = True
    include_outputs: bool = False
    include_attributes: bool = True
    include_extras: bool = True
    flat: bool = False
    dump_unsealed: bool = False


@dataclass
class ProfileDumpConfig:
    """Arguments for dumping profile data."""

    dump_processes: bool = True
    symlink_duplicates: bool = True
    delete_missing: bool = False
    extra_calc_dirs: bool = False
    organize_by_groups: bool = True
