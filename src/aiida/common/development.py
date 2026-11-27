###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Development-version confirmation for operations that modify an AiiDA installation."""

import typing as t
from os import PathLike

from aiida.common.exceptions import ConfirmationRequiredError

DEVELOPMENT_VERSION_WARNING_OPTION: t.Final = 'warnings.development_version'


def is_development_version() -> bool:
    """Return whether this is a 3.0.0 development snapshot or alpha prerelease."""
    from packaging.version import Version

    from aiida import __version__

    version = Version(__version__)
    return version.base_version == '3.0.0' and version.is_prerelease and (version.pre is None or version.pre[0] == 'a')


def require_development_version_acknowledgement(*, filepath: str | PathLike[str] | None = None) -> None:
    """Require a saved acknowledgement on development builds without prompting for input.

    :param filepath: read acknowledgement from this file instead of the active configuration
    :raises ConfirmationRequiredError: if the configuration does not contain an acknowledgement
    """
    if not is_development_version():
        return

    from aiida.manage.configuration import get_config_path
    from aiida.manage.configuration.config import Config

    if not Config.has_development_version_acknowledgement(filepath if filepath is not None else get_config_path()):
        msg = (
            'This AiiDA configuration has not acknowledged development-version risks. '
            'Run `verdi config set warnings.development_version False` to acknowledge them, '
            'or run `verdi config upgrade` if the configuration schema is outdated.'
        )
        raise ConfirmationRequiredError(msg)
