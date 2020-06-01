# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`CalcJob` implementation to add two numbers using bash for testing and demonstration purposes."""
import warnings

from aiida.common.warnings import AiidaDeprecationWarning
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation  # pylint: disable=unused-import

warnings.warn(  # pylint: disable=no-member
    'The add module has moved to aiida.calculations.arithmetic.add. '
    'This path will be removed in`v2.0.0`.', AiidaDeprecationWarning
)
