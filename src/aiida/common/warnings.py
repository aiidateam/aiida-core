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
    """Class for AiiDA deprecations.

    It does *not* inherit, on purpose, from `DeprecationWarning` as
    this would be filtered out by default.
    Enabled by default, you can disable it by running in the shell::

      verdi config warnings.showdeprecations False
    """


class AiidaEntryPointWarning(Warning):
    """Class for warnings concerning AiiDA entry points."""


class AiidaTestWarning(Warning):
    """Class for warnings concerning the AiiDA testing infrastructure."""


def warn_deprecation(message: str, version: int, stacklevel: int = 2) -> None:
    """Warn about a deprecation for a future aiida-core version.

    Warnings are emitted if the ``warnings.showdeprecations`` config option is set to ``True``. Its value can be
    overwritten with the ``AIIDA_WARN_v{version}`` environment variable. The exact value for the environment variable is
    irrelevant. Any value will mean the variable is enabled and warnings will be emitted.

    :param message: the message to be printed
    :param version: the major version number of the future version
    :param stacklevel: the stack level at which the warning is issued
    """
    from aiida.manage.configuration import get_config_option

    from_config = get_config_option('warnings.showdeprecations')
    from_environment = os.environ.get(f'AIIDA_WARN_v{version}')

    if from_config or from_environment:
        message = f'{message} (this will be removed in v{version})'
        warnings.warn(message, AiidaDeprecationWarning, stacklevel=stacklevel)
