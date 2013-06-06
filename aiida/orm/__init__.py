from aiida.orm.node import Node
from aiida.orm.calculation import Calculation
from aiida.orm.data import Data
from aiida.orm.code import Code
from aiida.orm.computer import Computer

def CalculationFactory(module):
    """
    Return a given subclass of Calculation, loading the correct plugin.
    
    Args:
        module: a string with the module of the calculation plugin to load, e.g.
        'quantumespresso.pw'.
    """
    from aiida.common.pluginloader import load_plugin 
    return load_plugin(Calculation, 'aiida.orm.calculation',module)
    
def DataFactory(module):
    """
    Return a given subclass of Data, loading the correct plugin.
    
    Args:
        module: a string with the module of the data plugin to load, e.g.
        'quantumespresso.pw'.
    """
    from aiida.common.pluginloader import load_plugin 
    return load_plugin(Data, 'aiida.orm.data', module)