###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Settings of a collab, stored as options of the profile that takes part in it."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

OPTION_ENABLED = 'collab.enabled'
OPTION_TOKEN = 'collab.token'
OPTION_BIND = 'collab.bind'
OPTION_PORT = 'collab.port'
