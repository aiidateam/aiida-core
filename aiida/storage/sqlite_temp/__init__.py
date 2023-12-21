###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A temporary backend, using an in-memory sqlite database.

This backend is intended for testing and demonstration purposes.
Whenever it is instantiated, it creates a fresh storage backend,
and destroys it when it is garbage collected.
"""

# AUTO-GENERATED

# fmt: off

from .backend import *

__all__ = (
    'SqliteTempBackend',
)

# fmt: on
