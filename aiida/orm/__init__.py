# from aiida.orm.impl import *

# To facilitate the renaming and do
# `from aiida.orm import CalculationFactory`.
from aiida.orm.impl import delete_computer
from aiida.orm.utils import *

from aiida.orm.calculation import Calculation
from aiida.orm.calculation.job import JobCalculation

def from_type_to_pluginclassname(typestr):
    """
    Return the string to pass to the load_plugin function, starting from
    the 'type' field of a Node.
    """
    # Fix for base class
    if typestr == "":
        typestr = "node.Node."
    if not typestr.endswith("."):
        raise DbContentError("The type name '{}' is not valid!".format(
            typestr))
    return typestr[:-1]  # Strip final dot

