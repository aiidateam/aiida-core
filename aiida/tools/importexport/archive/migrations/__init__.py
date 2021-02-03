# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration archive files from old export versions to the newest, used by `verdi export migrate` command."""
from pathlib import Path
from typing import Any, Callable, Dict, Tuple, Union

from aiida.tools.importexport.archive.common import CacheFolder

from .v01_to_v02 import migrate_v1_to_v2
from .v02_to_v03 import migrate_v2_to_v3
from .v03_to_v04 import migrate_v3_to_v4
from .v04_to_v05 import migrate_v4_to_v5
from .v05_to_v06 import migrate_v5_to_v6
from .v06_to_v07 import migrate_v6_to_v7
from .v07_to_v08 import migrate_v7_to_v8
from .v08_to_v09 import migrate_v8_to_v9
from .v09_to_v10 import migrate_v9_to_v10

# version from -> version to, function which acts on the cache folder
_vtype = Dict[str, Tuple[str, Callable[[CacheFolder], None]]]
MIGRATE_FUNCTIONS: _vtype = {
    '0.1': ('0.2', migrate_v1_to_v2),
    '0.2': ('0.3', migrate_v2_to_v3),
    '0.3': ('0.4', migrate_v3_to_v4),
    '0.4': ('0.5', migrate_v4_to_v5),
    '0.5': ('0.6', migrate_v5_to_v6),
    '0.6': ('0.7', migrate_v6_to_v7),
    '0.7': ('0.8', migrate_v7_to_v8),
    '0.8': ('0.9', migrate_v8_to_v9),
    '0.9': ('0.10', migrate_v9_to_v10)
}
