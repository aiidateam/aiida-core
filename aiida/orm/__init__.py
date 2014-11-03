# -*- coding: utf-8 -*-
from aiida.orm.node import Node
from aiida.orm.calculation import Calculation
from aiida.orm.data import Data
from aiida.orm.code import Code
from aiida.orm.computer import Computer
from aiida.orm.group import Group

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

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

