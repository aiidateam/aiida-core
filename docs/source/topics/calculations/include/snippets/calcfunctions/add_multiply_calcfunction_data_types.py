from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def add(x, y):
    return x + y


@calcfunction
def multiply(x, y):
    return x * y


result = multiply(add(Int(value=1), Int(value=2)), Int(value=3))
