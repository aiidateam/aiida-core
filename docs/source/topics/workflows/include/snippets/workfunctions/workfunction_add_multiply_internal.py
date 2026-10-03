from aiida.engine import workfunction
from aiida.orm import Int


@workfunction
def add_and_multiply(x, y, z):
    sum = Int(value=x + y)
    product = Int(value=sum * z)
    return product.store()


result = add_and_multiply(Int(value=1), Int(value=2), Int(value=3))
