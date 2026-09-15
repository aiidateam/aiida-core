from aiida.engine import workfunction
from aiida.orm import Int


@workfunction
def maximum(x, y, z):
    return sorted([x, y, z])[-1]


result = maximum(Int(value=1), Int(value=2), Int(value=3))
