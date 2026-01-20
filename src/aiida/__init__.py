###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA is a flexible and scalable informatics' infrastructure to manage,
preserve, and disseminate the simulations, data, and workflows of
modern-day computational science.

Able to store the full provenance of each object, and based on a
tailored database built for efficient data mining of heterogeneous results,
AiiDA gives the user the ability to interact seamlessly with any number of
remote HPC resources and codes, thanks to its flexible plugin interface
and workflow engine for the automation of complex sequences of simulations.

More information at http://www.aiida.net
"""

from aiida.common.log import configure_logging
from aiida.manage.configuration import get_config_option, get_profile, load_profile, profile_context

__copyright__ = (
    'Copyright (c), This file is part of the AiiDA platform. '
    'For further information please visit http://www.aiida.net/. All rights reserved.'
)
__license__ = 'MIT license, see LICENSE.txt file.'
__version__ = '2.7.3'
__authors__ = 'The AiiDA team.'
__paper__ = (
    'S. P. Huber et al., "AiiDA 1.0, a scalable computational infrastructure for automated reproducible workflows and '
    'data provenance", Scientific Data 7, 300 (2020); https://doi.org/10.1038/s41597-020-00638-4'
)
__paper_short__ = 'S. P. Huber et al., Scientific Data 7, 300 (2020).'

__all__ = [
    'configure_logging',
    'get_config_option',
    'get_file_header',
    'get_profile',
    'get_strict_version',
    'get_version',
    'load_ipython_extension',
    'load_profile',
    'profile_context',
]


def get_strict_version():
    """Return a distutils StrictVersion instance with the current distribution version

    :returns: StrictVersion instance with the current version
    :rtype: :class:`!distutils.version.StrictVersion`
    """
    import sys

    if sys.version_info >= (3, 12):
        msg = 'Cannot use get_strict_version() with Python 3.12 and newer'
        raise RuntimeError(msg)
    else:
        from distutils.version import StrictVersion

        from aiida.common.warnings import warn_deprecation

        warn_deprecation(
            'This method is deprecated as the `distutils` package it uses will be removed in Python 3.12.', version=3
        )
        return StrictVersion(__version__)


def get_version() -> str:
    """Return the current AiiDA distribution version

    :returns: the current version
    """
    return __version__


def _get_raw_file_header() -> str:
    """Get the default header for source AiiDA source code files.
    Note: is not preceded by comment character.

    :return: default AiiDA source file header
    """
    return f"""This file has been created with AiiDA v. {__version__}
If you use AiiDA for publication purposes, please cite:
{__paper__}
"""


def get_file_header(comment_char: str = '# ') -> str:
    """Get the default header for source AiiDA source code files.

    .. note::

        Prepend by comment character.

    :param comment_char: string put in front of each line

    :return: default AiiDA source file header
    """
    lines = _get_raw_file_header().splitlines()
    return '\n'.join(f'{comment_char}{line}' for line in lines)


def load_ipython_extension(ipython):
    """Load the AiiDA IPython extension, using ``%load_ext aiida``.

    :param ipython: InteractiveShell instance. If ``None``, the global InteractiveShell is used.
    """
    from aiida.tools.ipython.ipython_magics import load_ipython_extension

    load_ipython_extension(ipython)
