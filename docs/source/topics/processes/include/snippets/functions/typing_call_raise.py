from aiida.engine import calcfunction
from aiida.orm import Float, Int


@calcfunction
def add(x: Int, y: Int):
    return x + y


add(Int(1), Float(1.0))
