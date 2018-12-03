# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Legacy import path for the workfunction decorator."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import warnings

from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
from .process_function import workfunction

warnings.warn('this module has been deprecated, import directly from `aiida.work` instead', DeprecationWarning)  # pylint: disable=no-member

__all__ = ('workfunction',)
