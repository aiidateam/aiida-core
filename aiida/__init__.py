# -*- coding: utf-8 -*-
from aiida.djsite.utils import load_dbenv, is_dbenv_loaded

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi"
__paper__ = """G. Pizzi, A. Cepellotti, R. Sabatini, N. Marzari, and B. Kozinsky, "AiiDA: automated interactive infrastructure and database for computational science", Comp. Mat. Sci 111, 218-230 (2016); http://dx.doi.org/10.1016/j.commatsci.2015.09.013 - http://www.aiida.net."""
__paper_short__ = """G. Pizzi et al., Comp. Mat. Sci 111, 218 (2016)."""


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
