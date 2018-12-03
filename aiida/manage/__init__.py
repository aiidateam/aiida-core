# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
A module to bring together the different parts of AiIDA:

  * backend
  * profile/settings
  * daemon/workflow runner
  * etc.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=wildcard-import

from .manager import *

__all__ = manager.__all__  # pylint: disable=undefined-variable
