# -*- coding: utf-8 -*-
from aiida.orm.node import Node
from aiida.orm.calculation import Calculation
from aiida.orm.calculation.job import JobCalculation
from aiida.orm.data import Data
from aiida.orm.code import Code
from aiida.orm.computer import Computer
from aiida.orm.group import Group

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

def CalculationFactory(module, from_abstract=False):
    """
    Return a suitable JobCalculation subclass.
    
    :param module: a valid string recognized as a Calculation plugin
    :param from_abstract: A boolean. If False (default), actually look only
      to subclasses to JobCalculation, not to the base Calculation class.
      If True, check for valid strings for plugins of the Calculation base class.
    """
    from aiida.common.pluginloader import BaseFactory
    
    if from_abstract:
        return BaseFactory(module, Calculation, "aiida.orm.calculation")
    else:
        return BaseFactory(module, JobCalculation, "aiida.orm.calculation.job",
                           suffix="Calculation")

def DataFactory(module):
    """
    Return a suitable Data subclass.
    """
    from aiida.common.pluginloader import BaseFactory
    
    return BaseFactory(module, Data, "aiida.orm.data")

