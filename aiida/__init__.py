# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import warnings

from aiida.common.log import configure_logging
from aiida.common.setup import get_property

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.12.4"
__authors__ = "The AiiDA team."
__paper__ = """G. Pizzi, A. Cepellotti, R. Sabatini, N. Marzari, and B. Kozinsky, "AiiDA: automated interactive infrastructure and database for computational science", Comp. Mat. Sci 111, 218-230 (2016); http://dx.doi.org/10.1016/j.commatsci.2015.09.013 - http://www.aiida.net."""
__paper_short__ = """G. Pizzi et al., Comp. Mat. Sci 111, 218 (2016)."""

# Configure the default logging
configure_logging()

if get_property("warnings.showdeprecations"):
    # print out the warnings coming from deprecation
    # in Python 2.7 it is suppressed by default
    warnings.simplefilter('default', DeprecationWarning)


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
    from aiida.backends.utils import load_dbenv
    return load_dbenv(*argc, **argv)


def is_dbenv_loaded(*argc, **argv):
    """
    Alias for `is_dbenv_loaded` from `aiida.backends.utils`
    """
    from aiida.backends.utils import is_dbenv_loaded
    return is_dbenv_loaded(*argc, **argv)


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
