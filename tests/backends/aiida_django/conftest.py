# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Configuration file for pytest tests."""

from aiida.backends import BACKEND_DJANGO
from aiida.manage.tests import get_test_backend_name

if get_test_backend_name() != BACKEND_DJANGO:
    collect_ignore_glob = ['*']  # pylint: disable=invalid-name
