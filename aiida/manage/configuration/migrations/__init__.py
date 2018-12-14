# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=undefined-variable,wildcard-import
"""Methods and definitions of migrations for the configuration file of an AiiDA instance."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .migrations import *
from .utils import *

__all__ = (migrations.__all__ + utils.__all__)
