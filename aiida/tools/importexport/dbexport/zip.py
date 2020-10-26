# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Export a zip-file."""
# pylint: disable=redefined-builtin,unused-import
import warnings
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.tools.importexport.common.zip_folder import ZipFolder

warnings.warn(
    'This module is deprecated and will be removed in v2.0.0, use `aiida.tools.importexport.common.zip_folder` instead',
    AiidaDeprecationWarning
)  # pylint: disable=no-member
