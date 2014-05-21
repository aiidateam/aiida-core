from aiida.orm.node import Node
from aiida.orm.calculation import Calculation
from aiida.orm.data import Data
from aiida.orm.code import Code
from aiida.orm.computer import Computer

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

