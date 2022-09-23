# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=unused-import
"""A utility module with mapper objects that map database entities projections on attributes and labels."""
from aiida.common.warnings import warn_deprecation
from aiida.tools.query.mapping import CalculationProjectionMapper, ProjectionMapper

warn_deprecation('This module is deprecated, use `aiida.tools.query.mapping` instead.', version=3)
