# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for implementations of database backends.

.. deprecated:: 1.0.0
    Will be removed in `v1.1.0`, use :mod:`aiida.backends` instead.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import warnings

warnings.warn('this module is deprecated', DeprecationWarning)  # pylint: disable=no-member

# Possible choices for backend
BACKEND_DJANGO = 'django'
BACKEND_SQLA = 'sqlalchemy'
