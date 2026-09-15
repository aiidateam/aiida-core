from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def divide(x, y):
    return x / y


result = divide(Int(value=1), Int(value=0))
