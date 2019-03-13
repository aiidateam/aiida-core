# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=wildcard-import,undefined-variable
"""Classes and functions to load and interact with plugin classes accessible through defined entry points."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .entry_point import *
from .factories import *

__all__ = (entry_point.__all__ + factories.__all__)
