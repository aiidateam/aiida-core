# -*- coding: utf-8 -*-
from aiida.engine import calcfunction, workfunction
from aiida.orm import Int

@calcfunction
def add(x, y):
    return Int(x + y)

@workfunction
def add_and_multiply(x, y, z):
    sum = add(x, y)
    product = Int(sum * z)
    return product.store()

result = add_and_multiply(Int(1), Int(2), Int(3))
