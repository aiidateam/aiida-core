# -*- coding: utf-8 -*-
from aiida.djsite.utils import load_dbenv

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

def get_version():
    """
    Very simple function to get a string with the version number.
    """
    return __version__

__paper__ = "G. Pizzi, A. Cepellotti, R. Sabatini, N. Marzari and B. Kozinsky, to be submitted"

def get_file_header():
    """
    Get a string to be put as header of files created with AiiDA
    """
    return """# This file has been created with AiiDA v. {}
#  
# If you use AiiDA for publication purposes, please cite:
# {} 
""".format(__version__,__paper__)
