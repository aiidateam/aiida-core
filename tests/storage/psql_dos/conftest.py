# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Skip this test module unless the storage backend of the test profile matches ``core.psql_dos``."""
import os

from aiida.common.exceptions import MissingConfigurationError
from aiida.manage.configuration import get_config

try:
    STORAGE_BACKEND_ENTRY_POINT = get_config().get_profile(os.environ.get('AIIDA_TEST_PROFILE', None)).storage_backend
except MissingConfigurationError:
    # Case when ``pytest`` is invoked without existing config, in which case it will rely on the automatic test profile
    # creation which currently always uses ``core.psql_dos`` for the storage backend
    STORAGE_BACKEND_ENTRY_POINT = 'core.psql_dos'

if STORAGE_BACKEND_ENTRY_POINT != 'core.psql_dos':
    collect_ignore_glob = ['*']  # pylint: disable=invalid-name
