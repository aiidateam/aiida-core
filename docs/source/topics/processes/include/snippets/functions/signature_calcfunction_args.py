from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def average(*args):
    return sum(args) / len(args)


result = average(*(Int(value=1), Int(value=2), Int(value=3)))
