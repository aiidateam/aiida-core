###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Prefer the broker-aware project profile over the public plugin's no-broker fixture.

Local conftest fixtures take precedence when running these benchmarks with ``-p tests.conftest``.
"""

from tests.conftest import aiida_profile  # noqa: F401
