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

from aiida.tools.dumping.utils import do_filter_nodes


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


# TODO: Some of those are also needed for the CollectionDumper
@dataclass
class ProfileDumpConfig:
    """Arguments for dumping profile data."""

    # TODO: Possibly add profile as attribute here?
    dump_processes: bool = True
    symlink_duplicates: bool = False
    delete_missing: bool = False
    organize_by_groups: bool = True
    only_groups: bool = False
    only_top_level_calcs: bool = True
    only_top_level_workflows: bool = True
    filter_nodes_by_last_dump_time: bool = True
