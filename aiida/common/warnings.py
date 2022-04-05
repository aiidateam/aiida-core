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
import os
import warnings


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


def warn_deprecation(message: str, version: int, stacklevel=2) -> None:
    """Warns about a deprecation for a future aiida-core version.

    Warnings are activated if the `AIIDA_WARN_v{major}` environment variable is set to `True`.

    :param message: the message to be printed
    :param version: the major version number of the future version
    :param stacklevel: the stack level at which the warning is issued
    """
    if os.environ.get(f'AIIDA_WARN_v{version}'):
        message = f'{message} (this will be removed in v{version})'
        warnings.warn(message, AiidaDeprecationWarning, stacklevel=stacklevel)
