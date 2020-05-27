# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic `CalcJob` implementation where input file is a parametrized template file."""
import warnings

from aiida.common.warnings import AiidaDeprecationWarning
from aiida.calculations.templatereplacer import TemplatereplacerCalculation  # pylint: disable=unused-import

warnings.warn(  # pylint: disable=no-member
    'The templatereplacer module has moved to aiida.calculations.templatereplacer. '
    'This path will be removed in a future release.', AiidaDeprecationWarning
)
