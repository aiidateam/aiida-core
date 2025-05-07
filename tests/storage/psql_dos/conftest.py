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

STORAGE_BACKEND_ENTRY_POINT = None
try:
    if test_profile := os.environ.get('AIIDA_TEST_PROFILE'):
        STORAGE_BACKEND_ENTRY_POINT = get_config().get_profile(test_profile).storage_backend
except MissingConfigurationError as e:
    raise ValueError(f"Could not parse configuration of AiiDA test profile '{test_profile}'") from e

if STORAGE_BACKEND_ENTRY_POINT is not None and STORAGE_BACKEND_ENTRY_POINT != 'core.psql_dos':
    collect_ignore_glob = ['*']
