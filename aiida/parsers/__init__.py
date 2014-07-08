# -*- coding: utf-8 -*-
from aiida.parsers.parser import Parser

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

def ParserFactory(module):
    """
    Return a suitable Parser subclass.
    """
    from aiida.common.pluginloader import BaseFactory
    
    return BaseFactory(module, Parser, "aiida.parsers.plugins")