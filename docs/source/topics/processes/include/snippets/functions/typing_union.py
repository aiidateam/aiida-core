from aiida.engine import calcfunction
from aiida.orm import Float, Int


@calcfunction
def add(x: Int | Float, y: Int | Float):
    return x + y


add(Int(value=1), Float(value=1.0))
