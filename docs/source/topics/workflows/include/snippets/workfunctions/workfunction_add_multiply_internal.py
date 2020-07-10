# -*- coding: utf-8 -*-
from aiida.engine import calcfunction, workfunction
from aiida.orm import Int

@workfunction
def add_and_multiply(x, y, z):
    sum = Int(x + y)
    product = Int(sum * z)
    return product.store()

result = add_and_multiply(Int(1), Int(2), Int(3))
