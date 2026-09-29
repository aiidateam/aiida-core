from aiida.engine import workfunction
from aiida.orm import Int


@workfunction
def illegal_workfunction(x, y):
    return Int(value=x + y)


result = illegal_workfunction(Int(value=1), Int(value=2))
