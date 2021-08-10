# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Methods to validate the database integrity and fix violations."""

# AUTO-GENERATED
# yapf: disable
# pylint: disable=wildcard-import

from .duplicate_uuid import *
from .utils import *

__all__ = (
    'TABLES_UUID_DEDUPLICATION',
    'deduplicate_uuids',
    'get_duplicate_uuids',
    'verify_uuid_uniqueness',
    'write_database_integrity_violation',
)
