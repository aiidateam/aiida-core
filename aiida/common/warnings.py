# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Define warnings that can be thrown by AiiDA."""


class AiidaDeprecationWarning(Warning):
    """
    Class for AiiDA deprecations.

    It does *not* inherit, on purpose, from `DeprecationWarning` as
    this would be filtered out by default.
    Enabled by default, you can disable it by running in the shell::

      verdi config warnings.showdeprecations False
    """


class AiidaEntryPointWarning(Warning):
    """
    Class for warnings concerning AiiDA entry points.
    """


class AiidaTestWarning(Warning):
    """
    Class for warnings concerning the AiiDA testing infrastructure.
    """
