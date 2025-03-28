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
from enum import Enum, auto

__all__ = (
    "NodeMirrorGroupScope",
    "MirrorMode",
    "NodeCollectorConfig",
    "ProcessMirrorConfig",
    "BaseCollectionMirrorConfig",
    "GroupMirrorConfig",
    "ProfileMirrorConfig"
)


class NodeMirrorGroupScope(Enum):
    IN_GROUP = auto()
    ANY = auto()
    NO_GROUP = auto()


class MirrorMode(Enum):
    OVERWRITE = auto()
    INCREMENTAL = auto()
    DRY_RUN = auto()


@dataclass
class NodeCollectorConfig:
    """Shared arguments for dumping of collections of nodes."""

    # NOTE: Should the `last_mirror_time` also be here
    include_processes: bool = True
    include_data: bool = False
    filter_by_last_mirror_time: bool = True
    only_top_level_calcs: bool = True
    only_top_level_workflows: bool = True
    group_scope: NodeMirrorGroupScope = NodeMirrorGroupScope.IN_GROUP

@dataclass
class ProcessMirrorConfig:
    """Arguments for dumping process data."""

    include_inputs: bool = True
    include_outputs: bool = False
    include_attributes: bool = True
    include_extras: bool = True
    flat: bool = False
    mirror_unsealed: bool = False
    symlink_calcs: bool = False


@dataclass
class BaseCollectionMirrorConfig:
    symlink_calcs: bool = False
    delete_missing: bool = False


@dataclass
class GroupMirrorConfig(BaseCollectionMirrorConfig):  # NodeCollectorConfig
    """Arguments for dumping group data."""

    ...


@dataclass
class ProfileMirrorConfig(BaseCollectionMirrorConfig):  # NodeCollectorConfig
    """Arguments for dumping profile data."""

    organize_by_groups: bool = True
    only_groups: bool = False
    update_groups: bool = True
    symlink_between_groops: bool = False
