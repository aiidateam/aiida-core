###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import annotations

from dataclasses import dataclass

# TODO: Check if dataclasses are meant to

@dataclass
class BaseDumpConfig:
    """Container for shared base arguments of all Dumper classes."""

    overwrite: bool = False
    incremental: bool = True


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
class CollectionDumpConfig:
    """Shared arguments for dumping of collections of nodes."""
    dump_processes: bool = True
    symlink_duplicates: bool = False
    delete_missing: bool = False
    only_top_level_calcs: bool = True
    only_top_level_workflows: bool = True
    filter_by_last_dump_time: bool = True

@dataclass
class GroupDumpConfig(CollectionDumpConfig):
    """Arguments for dumping group data."""
    ...


@dataclass
class ProfileDumpConfig(CollectionDumpConfig):
    """Arguments for dumping profile data."""
    organize_by_groups: bool = True
    only_groups: bool = False
