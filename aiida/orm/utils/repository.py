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
"""Module shadowing original in order to print deprecation warning only when external code uses it."""
import warnings

from aiida.common import exceptions
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.repository import File, FileType
from ._repository import Repository as _Repository

warnings.warn(
    'this module is deprecated and will be removed in `v2.0.0`. '
    '`File` and `FileType` should be imported from `aiida.repository`.', AiidaDeprecationWarning
)


class Repository(_Repository):
    """Class shadowing original class in order to print deprecation warning when external code uses it."""

    def __init__(self, *args, **kwargs):
        warnings.warn('This class has been deprecated and will be removed in `v2.0.0`.', AiidaDeprecationWarning)  # pylint: disable=no-member"""
        super().__init__(*args, **kwargs)
