# -*- coding: utf-8 -*-
from aiida.orm.node import Node
from aiida.orm.calculation import Calculation
from aiida.orm.data import Data
from aiida.orm.code import Code
from aiida.orm.computer import Computer
from aiida.orm.group import Group

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

def CalculationFactory(module):
    """
    Return a suitable Calculation subclass.
    """
    from aiida.common.pluginloader import BaseFactory

    return BaseFactory(module, Calculation, "aiida.orm.calculation")

def DataFactory(module):
    """
    Return a suitable Data subclass.
    """
    from aiida.common.pluginloader import BaseFactory
    
    return BaseFactory(module, Data, "aiida.orm.data")

