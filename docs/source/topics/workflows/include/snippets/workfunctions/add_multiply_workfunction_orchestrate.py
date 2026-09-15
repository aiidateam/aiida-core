from aiida.engine import calcfunction, workfunction
from aiida.orm import Int


@calcfunction
def add(x, y):
    return Int(value=x + y)


@calcfunction
def multiply(x, y):
    return Int(value=x * y)


@workfunction
def add_and_multiply(x, y, z):
    sum = add(x, y)
    product = multiply(sum, z)
    return product


result = add_and_multiply(Int(value=1), Int(value=2), Int(value=3))
