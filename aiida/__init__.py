# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
AiiDA is a flexible and scalable informatics' infrastructure to manage,
preserve, and disseminate the simulations, data, and workflows of
modern-day computational science.

Able to store the full provenance of each object, and based on a
tailored database built for efficient data mining of heterogeneous results,
AiiDA gives the user the ability to interact seamlessly with any number of
remote HPC resources and codes, thanks to its flexible plugin interface
and workflow engine for the automation of complex sequences of simulations.

More information at http://www.aiida.net
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import warnings
import six

import aiida.common.warnings
from aiida.common.log import configure_logging
from aiida.manage.configuration import get_config_option

__copyright__ = (u'Copyright (c), This file is part of the AiiDA platform. '
                 u'For further information please visit http://www.aiida.net/. All rights reserved.')
__license__ = 'MIT license, see LICENSE.txt file.'
__version__ = '1.0.0b1'
__authors__ = 'The AiiDA team.'
__paper__ = (u'G. Pizzi, A. Cepellotti, R. Sabatini, N. Marzari, and B. Kozinsky,'
             u'"AiiDA: automated interactive infrastructure and database for computational science", '
             u'Comp. Mat. Sci 111, 218-230 (2016); http://dx.doi.org/10.1016/j.commatsci.2015.09.013 '
             u'- http://www.aiida.net.')
__paper_short__ = 'G. Pizzi et al., Comp. Mat. Sci 111, 218 (2016).'

# Configure the default logging
configure_logging()

if get_config_option('warnings.showdeprecations'):
    # If the user does not want to get AiiDA deprecation warnings, we disable them - this can be achieved with::
    #   verdi config warnings.showdeprecations False
    # Note that the AiidaDeprecationWarning does NOT inherit from DeprecationWarning
    warnings.simplefilter('default', aiida.common.warnings.AiidaDeprecationWarning)  # pylint: disable=no-member
    # This should default to 'once', i.e. once per different message
else:
    warnings.simplefilter('ignore', aiida.common.warnings.AiidaDeprecationWarning)  # pylint: disable=no-member

if six.PY2:
    warnings.warn('python 2 will be deprecated in `aiida-core v2.0.0`', DeprecationWarning)  # pylint: disable=no-member


def try_load_dbenv(*argc, **argv):
    """
    Run `load_dbenv` unless the dbenv has already been loaded.
    """
    if not is_dbenv_loaded():
        load_dbenv(*argc, **argv)
        return True
    return False


def load_dbenv(*argc, **argv):
    """
    Alias for `load_dbenv` from `aiida.backends.utils`
    """
    from aiida.backends.utils import load_dbenv as _load_dbenv
    return _load_dbenv(*argc, **argv)


def is_dbenv_loaded(*argc, **argv):
    """
    Alias for `is_dbenv_loaded` from `aiida.backends.utils`
    """
    from aiida.backends.utils import is_dbenv_loaded as _is_dbenv_loaded
    return _is_dbenv_loaded(*argc, **argv)


def get_strict_version():
    """
    Return a distutils StrictVersion instance with the current distribution version

    :returns: StrictVersion instance with the current version
    """
    from distutils.version import StrictVersion
    return StrictVersion(__version__)


def get_version():
    """
    Return the current distribution version

    :returns: a string with the current version
    """
    return __version__


def _get_raw_file_header():
    """
    Get a string to be put as header of files created with AiiDA; no
    comment character is put in front

    :return: a (multiline) string
    """
    return """This file has been created with AiiDA v. {}
If you use AiiDA for publication purposes, please cite:
{}
""".format(__version__, __paper__)


def get_file_header(comment_char="# "):
    """
    Get a string to be put as header of files created with AiiDA;
    put in front a comment character as specified in the parameter

    :param comment_char: string put in front of each line
    :return: a (multiline) string
    """
    lines = _get_raw_file_header().splitlines()
    return '\n'.join('{}{}'.format(comment_char, line) for line in lines)
