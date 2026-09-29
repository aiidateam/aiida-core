from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def add(x, y):
    result = Int(value=x + y).store()
    return result


result = add(Int(value=1), Int(value=2))
