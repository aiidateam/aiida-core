# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.orm.implementation.calculation import Calculation, JobCalculation
from .inline import *
from .work import WorkCalculation
from .function import FunctionCalculation

_local = 'Calculation', 'JobCalculation', 'WorkCalculation', 'FunctionCalculation'

__all__ = _local + inline.__all__
