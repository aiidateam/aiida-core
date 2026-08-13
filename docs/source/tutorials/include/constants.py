###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regexes for the ``gsrd`` stdout diagnostics parsed in module 2."""

import re

VARIANCE_RE = re.compile(r'Variance of V field\s*:\s*([\d.eE+-]+)')
"""Matches the ``Variance of V field : <value>`` diagnostic in ``gsrd`` stdout."""

MEAN_RE = re.compile(r'Mean\s+of V field\s*=\s*([\d.eE+-]+)')
"""Matches the ``Mean of V field = <value>`` diagnostic in ``gsrd`` stdout."""
