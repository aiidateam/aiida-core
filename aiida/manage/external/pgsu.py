# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Connect to an existing PostgreSQL cluster as the `postgres` superuser and execute SQL commands.

Note: Once the API of this functionality has converged, this module should be moved out of aiida-core and into a
  separate package that can then be tested on multiple OS / postgres setups. Therefore, **please keep this
  module entirely AiiDA-agnostic**.
"""
import warnings
from pgsu import PGSU, PostgresConnectionMode, DEFAULT_DSN as DEFAULT_DBINFO  # pylint: disable=unused-import,no-name-in-module
from aiida.common.warnings import AiidaDeprecationWarning

warnings.warn(  # pylint: disable=no-member
    '`aiida.manage.external.pgsu` is now available in the separate `pgsu` package. '
    'This module will be removed entirely in AiiDA 2.0.0', AiidaDeprecationWarning
)
