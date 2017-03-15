# -*- coding: utf-8 -*-
import warnings
from aiida.common.setup import get_property

__paper__ = """G. Pizzi, A. Cepellotti, R. Sabatini, N. Marzari, and B. Kozinsky, "AiiDA: automated interactive infrastructure and database for computational science", Comp. Mat. Sci 111, 218-230 (2016); http://dx.doi.org/10.1016/j.commatsci.2015.09.013 - http://www.aiida.net."""
__paper_short__ = """G. Pizzi et al., Comp. Mat. Sci 111, 218 (2016)."""


if get_property("warnings.showdeprecations"):
    # print out the warnings coming from deprecation
    # in Python 2.7 it is suppressed by default
    warnings.simplefilter('default', DeprecationWarning)


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


def get_version():
    """
    Very simple function to get a string with the version number.
    """
    return __version__


def get_file_header():
    """
    Get a string to be put as header of files created with AiiDA
    """
    return """# This file has been created with AiiDA v. {}
#
# If you use AiiDA for publication purposes, please cite:
# {}
""".format(__version__, __paper__)
