# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Legacy migrations,
using the old ``data.json`` format for storing the database.

These migrations simply manipulate the metadata and data in-place.
"""
from typing import Callable, Dict, Tuple

from .v04_to_v05 import migrate_v4_to_v5
from .v05_to_v06 import migrate_v5_to_v6
from .v06_to_v07 import migrate_v6_to_v7
from .v07_to_v08 import migrate_v7_to_v8
from .v08_to_v09 import migrate_v8_to_v9
from .v09_to_v10 import migrate_v9_to_v10
from .v10_to_v11 import migrate_v10_to_v11
from .v11_to_v12 import migrate_v11_to_v12
from .v12_to_v13 import migrate_v12_to_v13

# version from -> version to, function which modifies metadata, data in-place
LEGACY_MIGRATE_FUNCTIONS: Dict[str, Tuple[str, Callable[[dict, dict], None]]] = {
    '0.4': ('0.5', migrate_v4_to_v5),
    '0.5': ('0.6', migrate_v5_to_v6),
    '0.6': ('0.7', migrate_v6_to_v7),
    '0.7': ('0.8', migrate_v7_to_v8),
    '0.8': ('0.9', migrate_v8_to_v9),
    '0.9': ('0.10', migrate_v9_to_v10),
    '0.10': ('0.11', migrate_v10_to_v11),
    '0.11': ('0.12', migrate_v11_to_v12),
    '0.12': ('0.13', migrate_v12_to_v13),
}
FINAL_LEGACY_VERSION = '0.13'
